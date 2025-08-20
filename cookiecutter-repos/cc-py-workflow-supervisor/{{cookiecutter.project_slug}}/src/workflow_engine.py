"""
Workflow Engine for Python Agents on Cloudflare Workers
Manages workflow execution logic and step coordination
"""

import asyncio
import json
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime

# Cloudflare Workers FFI imports
from js import console, fetch


class WorkflowEngine:
    """Manages workflow execution logic and step coordination."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the workflow engine."""
        self.steps = config.get('steps', [])
        self.agents = config.get('agents', [])
        self.strategy = config.get('strategy', 'sequential')
        self.error_handling = config.get('error_handling', 'retry_with_fallback')
        self.max_retries = config.get('max_retries', 3)
        self.timeout = config.get('timeout', 30000)
        
        # Track execution metrics
        self.metrics = {
            'total_executions': 0,
            'successful_executions': 0,
            'failed_executions': 0,
            'average_execution_time': 0,
            'step_metrics': {}
        }
    
    def validate_workflow(self) -> Dict[str, Any]:
        """Validate workflow configuration."""
        errors = []
        
        # Check for required agents
        for step in self.steps:
            agent = self.find_agent(step.get('agent', ''))
            if not agent:
                errors.append(f"Agent '{step.get('agent')}' required by step '{step.get('name')}' not found")
        
        # Check for circular dependencies
        if self.has_circular_dependencies():
            errors.append('Workflow contains circular dependencies')
        
        return {
            'valid': len(errors) == 0,
            'errors': errors
        }
    
    def has_circular_dependencies(self) -> bool:
        """Check for circular dependencies in workflow."""
        visited = set()
        recursion_stack = set()
        
        def has_cycle(step_name: str) -> bool:
            visited.add(step_name)
            recursion_stack.add(step_name)
            
            step = self.find_step(step_name)
            if step and 'depends_on' in step:
                for dep in step['depends_on']:
                    if dep not in visited:
                        if has_cycle(dep):
                            return True
                    elif dep in recursion_stack:
                        return True
            
            recursion_stack.discard(step_name)
            return False
        
        for step in self.steps:
            if step['name'] not in visited:
                if has_cycle(step['name']):
                    return True
        
        return False
    
    def get_execution_order(self) -> List[str]:
        """Get execution order based on dependencies."""
        order = []
        visited = set()
        
        def visit(step_name: str):
            if step_name in visited:
                return
            visited.add(step_name)
            
            step = self.find_step(step_name)
            if step and 'depends_on' in step:
                for dep in step['depends_on']:
                    visit(dep)
            
            order.append(step_name)
        
        for step in self.steps:
            visit(step['name'])
        
        return order
    
    async def execute(self, context: Dict[str, Any], strategy: Optional[str] = None) -> Dict[str, Any]:
        """Execute workflow with given strategy."""
        start_time = self.get_current_time_ms()
        self.metrics['total_executions'] += 1
        
        try:
            execution_strategy = strategy or self.strategy
            
            if execution_strategy == 'sequential':
                result = await self.execute_sequential(context)
            elif execution_strategy == 'parallel':
                result = await self.execute_parallel(context)
            elif execution_strategy == 'conditional':
                result = await self.execute_conditional(context)
            elif execution_strategy == 'map_reduce':
                result = await self.execute_map_reduce(context)
            else:
                raise Exception(f"Unknown strategy: {execution_strategy}")
            
            self.metrics['successful_executions'] += 1
            self.update_metrics(self.get_current_time_ms() - start_time)
            
            return result
            
        except Exception as error:
            self.metrics['failed_executions'] += 1
            raise error
    
    async def execute_sequential(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute steps sequentially."""
        results = {}
        execution_order = self.get_execution_order()
        
        for step_name in execution_order:
            step = self.find_step(step_name)
            if not step:
                continue
            
            # Check if step should be executed
            if not self.should_execute_step(step, results):
                continue
            
            # Execute step
            step_result = await self.execute_step(step, context, results)
            results[step_name] = step_result
            
            # Check if we should continue
            if step_result.get('stop_workflow', False):
                break
        
        return results
    
    async def execute_parallel(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute steps in parallel."""
        parallel_groups = self.get_parallel_groups()
        results = {}
        
        for group in parallel_groups:
            async def execute_step_task(step_name: str):
                step = self.find_step(step_name)
                if not step or not self.should_execute_step(step, results):
                    return None
                
                result = await self.execute_step(step, context, results)
                return {'step_name': step_name, 'result': result}
            
            # Execute group in parallel
            group_tasks = [execute_step_task(step_name) for step_name in group]
            group_results = await asyncio.gather(*group_tasks, return_exceptions=True)
            
            # Process group results
            for result in group_results:
                if result and not isinstance(result, Exception):
                    results[result['step_name']] = result['result']
        
        return results
    
    async def execute_conditional(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute steps conditionally."""
        results = {}
        
        for step in self.steps:
            # Evaluate condition
            if not self.evaluate_condition(step.get('condition'), context, results):
                continue
            
            # Execute step
            step_result = await self.execute_step(step, context, results)
            results[step['name']] = step_result
            
            # Update context for next conditions
            context = {**context, **step_result}
        
        return results
    
    async def execute_map_reduce(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute map-reduce pattern."""
        # Map phase
        map_steps = [step for step in self.steps if step.get('phase') == 'map']
        map_tasks = [self.execute_step(step, context, {}) for step in map_steps]
        
        map_results = await asyncio.gather(*map_tasks, return_exceptions=True)
        
        # Reduce phase
        reduce_step = next((step for step in self.steps if step.get('phase') == 'reduce'), None)
        if reduce_step:
            reduce_context = {**context, 'map_results': map_results}
            reduce_result = await self.execute_step(reduce_step, reduce_context, {})
            
            return {
                'map': map_results,
                'reduce': reduce_result
            }
        
        return {'map': map_results}
    
    async def execute_step(self, step: Dict[str, Any], context: Dict[str, Any], previous_results: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single step."""
        start_time = self.get_current_time_ms()
        step_name = step['name']
        
        # Initialize step metrics
        if step_name not in self.metrics['step_metrics']:
            self.metrics['step_metrics'][step_name] = {
                'executions': 0,
                'failures': 0,
                'total_time': 0
            }
        
        step_metrics = self.metrics['step_metrics'][step_name]
        
        try:
            # Find the agent for this step
            agent = self.find_agent(step.get('agent', ''))
            if not agent:
                raise Exception(f"Agent {step.get('agent')} not found")
            
            # Prepare step context
            step_context = {
                **context,
                'previous_results': previous_results,
                'step_config': step
            }
            
            # Execute with timeout
            result = await self.execute_with_timeout(
                self.call_agent(agent, step_context),
                step.get('timeout', self.timeout)
            )
            
            # Update metrics
            step_metrics['executions'] += 1
            step_metrics['total_time'] += self.get_current_time_ms() - start_time
            
            return result
            
        except Exception as error:
            step_metrics['failures'] += 1
            
            # Handle error based on configuration
            if step.get('required', True):
                raise error
            
            return {'error': str(error), 'skipped': False}
    
    async def call_agent(self, agent: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Call an agent."""
        try:
            response = await fetch(agent['endpoint'], {
                'method': 'POST',
                'headers': {
                    'Content-Type': 'application/json',
                    **agent.get('headers', {})
                },
                'body': json.dumps(context)
            })
            
            if not response.ok:
                raise Exception(f"Agent {agent['name']} returned {response.status}")
            
            return await response.json()
            
        except Exception as error:
            raise Exception(f"Agent call failed: {str(error)}")
    
    async def execute_with_timeout(self, coro, timeout_ms: int):
        """Execute coroutine with timeout."""
        try:
            return await asyncio.wait_for(coro, timeout=timeout_ms / 1000)
        except asyncio.TimeoutError:
            raise Exception('Operation timed out')
    
    def should_execute_step(self, step: Dict[str, Any], previous_results: Dict[str, Any]) -> bool:
        """Check if step should be executed."""
        # Check dependencies
        if 'depends_on' in step:
            for dep in step['depends_on']:
                if dep not in previous_results or previous_results[dep].get('error'):
                    return False
        
        # Check condition
        if 'condition' in step:
            return self.evaluate_condition(step['condition'], {}, previous_results)
        
        return True
    
    def evaluate_condition(self, condition: Optional[str], context: Dict[str, Any], results: Dict[str, Any]) -> bool:
        """Evaluate a condition."""
        if not condition:
            return True
        
        try:
            # Simple condition evaluation (can be extended)
            # For safety, we only allow basic comparisons
            safe_globals = {
                'context': context,
                'results': results,
                'len': len,
                'str': str,
                'int': int,
                'float': float,
                'bool': bool
            }
            
            return bool(eval(condition, {"__builtins__": {}}, safe_globals))
            
        except Exception as error:
            console.error('Condition evaluation failed:', str(error))
            return False
    
    def get_parallel_groups(self) -> List[List[str]]:
        """Get parallel execution groups."""
        groups = []
        visited = set()
        
        # Group steps that can run in parallel
        for step in self.steps:
            if step['name'] in visited:
                continue
            
            group = [step['name']]
            visited.add(step['name'])
            
            # Find other steps that can run in parallel
            for other in self.steps:
                if other['name'] in visited:
                    continue
                if not self.depends_on(other, step) and not self.depends_on(step, other):
                    group.append(other['name'])
                    visited.add(other['name'])
            
            groups.append(group)
        
        return groups
    
    def depends_on(self, step_a: Dict[str, Any], step_b: Dict[str, Any]) -> bool:
        """Check if step A depends on step B."""
        if 'depends_on' not in step_a:
            return False
        
        if step_b['name'] in step_a['depends_on']:
            return True
        
        # Check transitive dependencies
        for dep in step_a['depends_on']:
            dep_step = self.find_step(dep)
            if dep_step and self.depends_on(dep_step, step_b):
                return True
        
        return False
    
    def update_metrics(self, execution_time: int):
        """Update execution metrics."""
        total = self.metrics['successful_executions']
        current_avg = self.metrics['average_execution_time']
        
        self.metrics['average_execution_time'] = (current_avg * (total - 1) + execution_time) / total
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get workflow metrics."""
        return {
            **self.metrics,
            'success_rate': (
                self.metrics['successful_executions'] / self.metrics['total_executions']
                if self.metrics['total_executions'] > 0 else 0
            )
        }
    
    def find_step(self, step_name: str) -> Optional[Dict[str, Any]]:
        """Find step by name."""
        return next((step for step in self.steps if step['name'] == step_name), None)
    
    def find_agent(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Find agent by name."""
        return next((agent for agent in self.agents if agent['name'] == agent_name), None)
    
    def get_current_time_ms(self) -> int:
        """Get current time in milliseconds."""
        return int(datetime.now().timestamp() * 1000)