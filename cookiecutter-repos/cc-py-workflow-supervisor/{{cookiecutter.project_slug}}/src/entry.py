"""
{{ cookiecutter.project_name }}
{{ cookiecutter.description }}

This supervisor orchestrates multi-agent workflows on Cloudflare Workers with Pyodide runtime
"""

import json
import asyncio
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Union

# Cloudflare Workers FFI imports
from js import console, fetch, Response
from js import crypto as js_crypto

# Local imports
from base_agent import BaseAgent
from workflow_engine import WorkflowEngine  
from state_manager import StateManager


class {{ cookiecutter.agent_class_name }}(BaseAgent):
    """Workflow supervisor that orchestrates multi-agent systems."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the workflow supervisor."""
        
        # Supervisor configuration
        supervisor_config = {
            'name': '{{ cookiecutter.project_name }}',
            'description': '{{ cookiecutter.description }}',
            'icon': '🎭',
            'subtitle': 'Orchestrating multi-agent workflows',
            'system_prompt': """You are a workflow supervisor that orchestrates multi-agent systems.

Your responsibilities:
1. Analyze incoming requests and determine the appropriate workflow
2. Coordinate specialist agents to complete workflow steps
3. Monitor workflow progress and handle errors
4. Aggregate results from multiple agents
5. Ensure workflow completion or graceful failure

Workflow strategy: {{ cookiecutter.supervisor_strategy }}
Error handling: {{ cookiecutter.error_handling }}

Available workflow steps:
{{ cookiecutter.workflow_steps_json }}

Available specialist agents:
{{ cookiecutter.specialist_agents_json }}

Provide clear status updates and aggregate results from all agents.""",
            'placeholder': 'Describe your complex task...',
            'ai_label': 'Workflow Supervisor',
            'model': '{{ cookiecutter.ai_model }}',
            'max_tokens': {{ cookiecutter.max_tokens }},
            'temperature': {{ cookiecutter.temperature }},
            'cache_enabled': True,
            'cache_ttl': {{ cookiecutter.cache_ttl }},
            **(config or {})
        }
        
        super().__init__(supervisor_config)
        
        # Initialize workflow components
        self.workflow_steps = {{ cookiecutter.workflow_steps_json }}
        self.specialist_agents = {{ cookiecutter.specialist_agents_json }}
        self.supervisor_strategy = '{{ cookiecutter.supervisor_strategy }}'
        self.error_handling = '{{ cookiecutter.error_handling }}'
        self.max_retries = {{ cookiecutter.max_retries }}
        self.timeout_ms = {{ cookiecutter.timeout_ms }}
        
        # Initialize workflow engine and state manager
        self.workflow_engine = WorkflowEngine({
            'steps': self.workflow_steps,
            'agents': self.specialist_agents,
            'strategy': self.supervisor_strategy,
            'error_handling': self.error_handling,
            'max_retries': self.max_retries,
            'timeout': self.timeout_ms
        })
        
        self.state_manager = StateManager()
    
    async def process_question(self, env: Any, question: str) -> Dict[str, Any]:
        """Process request through workflow."""
        workflow_id = self.generate_uuid()
        
        try:
            # Initialize workflow state
            state = await self.state_manager.initialize_workflow(workflow_id, {
                'question': question,
                'strategy': self.supervisor_strategy,
                'steps': self.workflow_steps
            })
            
            # Analyze request and determine workflow
            analysis = await self.analyze_request(env, question)
            
            # Execute workflow based on strategy
            if self.supervisor_strategy == 'sequential':
                result = await self.execute_sequential_workflow(env, workflow_id, question, analysis)
            elif self.supervisor_strategy == 'parallel':
                result = await self.execute_parallel_workflow(env, workflow_id, question, analysis)
            elif self.supervisor_strategy == 'conditional':
                result = await self.execute_conditional_workflow(env, workflow_id, question, analysis)
            elif self.supervisor_strategy == 'map_reduce':
                result = await self.execute_map_reduce_workflow(env, workflow_id, question, analysis)
            else:
                result = await self.execute_sequential_workflow(env, workflow_id, question, analysis)
            
            # Update final state
            await self.state_manager.complete_workflow(workflow_id, result)
            
            return {
                'response': result['aggregated_response'],
                'workflow_id': workflow_id,
                'completed_steps': result['completed_steps'],
                'duration': result['duration'],
                'metadata': {
                    'strategy': self.supervisor_strategy,
                    'steps_executed': result['steps_executed'],
                    'errors': result['errors']
                }
            }
            
        except Exception as error:
            console.error('Workflow execution error:', str(error))
            await self.state_manager.fail_workflow(workflow_id, error)
            
            # Apply error handling strategy
            return await self.handle_workflow_error(env, workflow_id, error, question)
    
    async def analyze_request(self, env: Any, question: str) -> Dict[str, Any]:
        """Analyze request to determine workflow path."""
        prompt = f"""Analyze this request and determine the appropriate workflow steps:

Request: {question}

Available steps: {json.dumps(self.workflow_steps)}
Available agents: {json.dumps(self.specialist_agents)}

Provide a JSON response with:
1. requiredSteps: Array of step names to execute
2. reasoning: Brief explanation of workflow choice
3. expectedDuration: Estimated time in ms
4. complexity: low/medium/high
"""
        
        try:
            response = await self.call_llm(env, prompt)
            parsed_response = json.loads(response)
            return parsed_response
        except (json.JSONDecodeError, Exception):
            # Fallback to default workflow
            return {
                'requiredSteps': [step['name'] for step in self.workflow_steps],
                'reasoning': 'Executing default workflow',
                'expectedDuration': self.timeout_ms,
                'complexity': 'medium'
            }
    
    async def execute_sequential_workflow(self, env: Any, workflow_id: str, question: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute sequential workflow."""
        start_time = self.get_current_time_ms()
        completed_steps = []
        step_results = {}
        errors = []
        
        for step_name in analysis['requiredSteps']:
            step_config = self.find_step_config(step_name)
            if not step_config:
                continue
            
            try:
                # Update state for current step
                await self.state_manager.start_step(workflow_id, step_name)
                
                # Execute step with appropriate agent
                agent = self.find_agent_config(step_config['agent'])
                if not agent:
                    raise Exception(f"Agent {step_config['agent']} not found for step {step_name}")
                
                # Call specialist agent
                step_result = await self.call_specialist_agent(agent, question, step_results, env)
                
                step_results[step_name] = step_result
                completed_steps.append(step_name)
                
                # Update state with step completion
                await self.state_manager.complete_step(workflow_id, step_name, step_result)
                
            except Exception as error:
                console.error(f"Step {step_name} failed:", str(error))
                errors.append({'step': step_name, 'error': str(error)})
                
                # Handle step failure based on strategy
                if self.error_handling == 'retry_with_fallback':
                    retry_result = await self.retry_step(step_name, step_config, question, step_results, env)
                    if retry_result['success']:
                        step_results[step_name] = retry_result['data']
                        completed_steps.append(step_name)
                    elif step_config.get('required', True):
                        raise Exception(f"Required step {step_name} failed after retries")
                elif step_config.get('required', True):
                    raise error
        
        # Aggregate results
        aggregated_response = await self.aggregate_results(step_results, question, env)
        
        return {
            'aggregated_response': aggregated_response,
            'completed_steps': completed_steps,
            'steps_executed': len(step_results),
            'duration': self.get_current_time_ms() - start_time,
            'errors': errors,
            'step_results': step_results
        }
    
    async def execute_parallel_workflow(self, env: Any, workflow_id: str, question: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute parallel workflow."""
        start_time = self.get_current_time_ms()
        
        # Create tasks for all steps
        async def execute_step_task(step_name: str):
            step_config = self.find_step_config(step_name)
            if not step_config:
                return None
            
            agent = self.find_agent_config(step_config['agent'])
            if not agent:
                return None
            
            try:
                await self.state_manager.start_step(workflow_id, step_name)
                result = await self.call_specialist_agent(agent, question, {}, env)
                await self.state_manager.complete_step(workflow_id, step_name, result)
                return {'step': step_name, 'result': result, 'success': True}
            except Exception as error:
                return {'step': step_name, 'error': str(error), 'success': False}
        
        # Execute all steps in parallel
        tasks = [execute_step_task(step_name) for step_name in analysis['requiredSteps']]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        step_results = {}
        completed_steps = []
        errors = []
        
        for result in results:
            if not result or isinstance(result, Exception):
                continue
            if result['success']:
                step_results[result['step']] = result['result']
                completed_steps.append(result['step'])
            else:
                errors.append({'step': result['step'], 'error': result['error']})
        
        # Aggregate results
        aggregated_response = await self.aggregate_results(step_results, question, env)
        
        return {
            'aggregated_response': aggregated_response,
            'completed_steps': completed_steps,
            'steps_executed': len(step_results),
            'duration': self.get_current_time_ms() - start_time,
            'errors': errors,
            'step_results': step_results
        }
    
    async def execute_conditional_workflow(self, env: Any, workflow_id: str, question: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute conditional workflow."""
        # Implementation for conditional workflow execution
        # Evaluates conditions to determine next steps
        return await self.execute_sequential_workflow(env, workflow_id, question, analysis)
    
    async def execute_map_reduce_workflow(self, env: Any, workflow_id: str, question: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Execute map-reduce workflow."""
        start_time = self.get_current_time_ms()
        
        # Map phase: distribute work
        map_tasks = [
            {'agent': agent, 'task': self.create_map_task(question, agent)}
            for agent in self.specialist_agents
        ]
        
        # Execute map tasks in parallel
        async def execute_map_task(task):
            try:
                return await self.call_specialist_agent(task['agent'], task['task'], {}, env)
            except Exception as error:
                return {'error': str(error), 'agent': task['agent']['name']}
        
        map_results = await asyncio.gather(
            *[execute_map_task(task) for task in map_tasks],
            return_exceptions=True
        )
        
        # Reduce phase: aggregate results
        aggregated_response = await self.reduce_results(map_results, question, env)
        
        return {
            'aggregated_response': aggregated_response,
            'completed_steps': ['map', 'reduce'],
            'steps_executed': len(map_tasks) + 1,
            'duration': self.get_current_time_ms() - start_time,
            'errors': [r for r in map_results if isinstance(r, dict) and 'error' in r],
            'step_results': {'map': map_results, 'reduce': aggregated_response}
        }
    
    async def call_specialist_agent(self, agent: Dict[str, Any], question: str, context: Dict[str, Any], env: Any) -> Dict[str, Any]:
        """Call a specialist agent."""
        timeout = agent.get('timeout', 10000)
        retries = agent.get('retries', self.max_retries)
        
        for attempt in range(retries):
            try:
                # Prepare request body
                body = json.dumps({
                    'question': question,
                    'context': context,
                    'workflowMetadata': {
                        'supervisor': '{{ cookiecutter.project_name }}',
                        'strategy': self.supervisor_strategy
                    }
                })
                
                # Create request options
                headers = {'Content-Type': 'application/json'}
                headers.update(agent.get('headers', {}))
                
                # Make request using FFI fetch
                response = await fetch(agent['endpoint'], {
                    'method': 'POST',
                    'headers': headers,
                    'body': body
                })
                
                if not response.ok:
                    raise Exception(f"Agent {agent['name']} returned {response.status}")
                
                result = await response.json()
                return result
                
            except Exception as error:
                console.error(f"Agent {agent['name']} attempt {attempt + 1} failed:", str(error))
                if attempt == retries - 1:
                    raise error
                await asyncio.sleep((attempt + 1))  # Exponential backoff
    
    async def retry_step(self, step_name: str, step_config: Dict[str, Any], question: str, context: Dict[str, Any], env: Any) -> Dict[str, Any]:
        """Retry a failed step."""
        for attempt in range(self.max_retries):
            try:
                agent = self.find_agent_config(step_config['agent'])
                result = await self.call_specialist_agent(agent, question, context, env)
                return {'success': True, 'data': result}
            except Exception as error:
                console.error(f"Retry {attempt + 1} for step {step_name} failed:", str(error))
        
        return {'success': False}
    
    async def aggregate_results(self, step_results: Dict[str, Any], question: str, env: Any) -> str:
        """Aggregate results from multiple agents."""
        prompt = f"""Aggregate and synthesize these workflow results into a comprehensive response:

Original Question: {question}

Step Results:
{json.dumps(step_results, indent=2)}

Provide a unified, coherent response that:
1. Addresses the original question completely
2. Incorporates insights from all workflow steps
3. Highlights key findings and recommendations
4. Notes any conflicts or uncertainties
"""
        
        response = await self.call_llm(env, prompt)
        return response
    
    def create_map_task(self, question: str, agent: Dict[str, Any]) -> str:
        """Create map task for agent."""
        return f"Process this question from your perspective as {agent.get('description', agent['name'])}: {question}"
    
    async def reduce_results(self, map_results: List[Any], question: str, env: Any) -> str:
        """Reduce results from map phase."""
        valid_results = [r for r in map_results if not (isinstance(r, dict) and 'error' in r)]
        
        step_results = {}
        for i, result in enumerate(valid_results):
            step_results[f'map_{i}'] = result
        
        return await self.aggregate_results(step_results, question, env)
    
    async def handle_workflow_error(self, env: Any, workflow_id: str, error: Exception, question: str) -> Dict[str, Any]:
        """Handle workflow errors."""
        console.error(f"Workflow {workflow_id} failed:", str(error))
        
        if self.error_handling == 'retry_with_fallback':
            return {
                'response': f"I encountered an error processing your request. {str(error)}. Please try rephrasing or simplifying your request.",
                'workflow_id': workflow_id,
                'error': str(error),
                'status': 'failed_with_fallback'
            }
        elif self.error_handling == 'circuit_breaker':
            return {
                'response': 'The workflow system is temporarily unavailable. Please try again later.',
                'workflow_id': workflow_id,
                'error': 'Circuit breaker activated',
                'status': 'circuit_broken'
            }
        elif self.error_handling == 'compensate':
            await self.compensate_workflow(workflow_id)
            return {
                'response': 'The workflow failed and has been rolled back. Please try again.',
                'workflow_id': workflow_id,
                'error': str(error),
                'status': 'compensated'
            }
        else:
            return {
                'response': f"Workflow execution failed: {str(error)}",
                'workflow_id': workflow_id,
                'error': str(error),
                'status': 'failed'
            }
    
    async def compensate_workflow(self, workflow_id: str) -> None:
        """Compensate for failed workflow."""
        state = await self.state_manager.get_workflow_state(workflow_id)
        console.log(f"Compensating workflow {workflow_id}", state)
    
    async def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow status."""
        return await self.state_manager.get_workflow_state(workflow_id)
    
    def find_step_config(self, step_name: str) -> Optional[Dict[str, Any]]:
        """Find step configuration by name."""
        return next((step for step in self.workflow_steps if step['name'] == step_name), None)
    
    def find_agent_config(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Find agent configuration by name."""
        return next((agent for agent in self.specialist_agents if agent['name'] == agent_name), None)
    
    def generate_uuid(self) -> str:
        """Generate UUID using Cloudflare Workers crypto API."""
        # Use JavaScript crypto.randomUUID() via FFI
        return js_crypto.randomUUID()
    
    def get_current_time_ms(self) -> int:
        """Get current time in milliseconds."""
        return int(datetime.now().timestamp() * 1000)


# Export handler for Cloudflare Workers
async def on_fetch(request, env, context):
    """Cloudflare Workers fetch handler."""
    supervisor = {{ cookiecutter.agent_class_name }}()
    return await supervisor.handle_request(request, env, context)