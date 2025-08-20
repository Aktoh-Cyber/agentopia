"""
State Manager for Python Agents on Cloudflare Workers
Manages workflow state and persistence using KV storage
"""

import json
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

# Cloudflare Workers FFI imports
from js import console


class StateManager:
    """Manages workflow state and persistence."""
    
    def __init__(self, kv_namespace: Optional[Any] = None):
        """Initialize the state manager."""
        self.kv_namespace = kv_namespace
        self.in_memory_state = {}
        self.state_history = {}
    
    async def initialize_workflow(self, workflow_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize a new workflow."""
        state = {
            'workflow_id': workflow_id,
            'status': 'initialized',
            'start_time': datetime.now().isoformat(),
            'config': config,
            'current_step': None,
            'completed_steps': [],
            'failed_steps': [],
            'step_results': {},
            'errors': [],
            'metadata': {},
            'checkpoints': []
        }
        
        await self.save_state(workflow_id, state)
        return state
    
    async def start_step(self, workflow_id: str, step_name: str) -> Dict[str, Any]:
        """Start a workflow step."""
        state = await self.get_state(workflow_id)
        if not state:
            raise Exception(f"Workflow {workflow_id} not found")
        
        state['current_step'] = step_name
        state['step_results'][step_name] = {
            'status': 'in_progress',
            'start_time': datetime.now().isoformat()
        }
        
        await self.save_state(workflow_id, state)
        return state
    
    async def complete_step(self, workflow_id: str, step_name: str, result: Any) -> Dict[str, Any]:
        """Complete a workflow step."""
        state = await self.get_state(workflow_id)
        if not state:
            raise Exception(f"Workflow {workflow_id} not found")
        
        state['completed_steps'].append(step_name)
        
        current_time = datetime.now().isoformat()
        start_time = state['step_results'][step_name]['start_time']
        
        state['step_results'][step_name] = {
            **state['step_results'][step_name],
            'status': 'completed',
            'end_time': current_time,
            'result': result,
            'duration': self.calculate_duration(start_time, current_time)
        }
        
        # Clear current step if it matches
        if state['current_step'] == step_name:
            state['current_step'] = None
        
        await self.save_state(workflow_id, state)
        return state
    
    async def fail_step(self, workflow_id: str, step_name: str, error: Exception) -> Dict[str, Any]:
        """Fail a workflow step."""
        state = await self.get_state(workflow_id)
        if not state:
            raise Exception(f"Workflow {workflow_id} not found")
        
        state['failed_steps'].append(step_name)
        state['errors'].append({
            'step': step_name,
            'error': str(error),
            'timestamp': datetime.now().isoformat()
        })
        
        state['step_results'][step_name] = {
            **state['step_results'][step_name],
            'status': 'failed',
            'end_time': datetime.now().isoformat(),
            'error': str(error)
        }
        
        # Clear current step if it matches
        if state['current_step'] == step_name:
            state['current_step'] = None
        
        await self.save_state(workflow_id, state)
        return state
    
    async def complete_workflow(self, workflow_id: str, result: Any) -> Dict[str, Any]:
        """Complete entire workflow."""
        state = await self.get_state(workflow_id)
        if not state:
            raise Exception(f"Workflow {workflow_id} not found")
        
        end_time = datetime.now().isoformat()
        
        state['status'] = 'completed'
        state['end_time'] = end_time
        state['result'] = result
        state['duration'] = self.calculate_duration(state['start_time'], end_time)
        
        await self.save_state(workflow_id, state)
        await self.archive_workflow(workflow_id)
        
        return state
    
    async def fail_workflow(self, workflow_id: str, error: Exception) -> Dict[str, Any]:
        """Fail entire workflow."""
        state = await self.get_state(workflow_id)
        if not state:
            raise Exception(f"Workflow {workflow_id} not found")
        
        end_time = datetime.now().isoformat()
        
        state['status'] = 'failed'
        state['end_time'] = end_time
        state['error'] = str(error)
        state['duration'] = self.calculate_duration(state['start_time'], end_time)
        
        await self.save_state(workflow_id, state)
        await self.archive_workflow(workflow_id)
        
        return state
    
    async def create_checkpoint(self, workflow_id: str, checkpoint_name: str) -> Dict[str, Any]:
        """Create a checkpoint."""
        state = await self.get_state(workflow_id)
        if not state:
            raise Exception(f"Workflow {workflow_id} not found")
        
        checkpoint = {
            'name': checkpoint_name,
            'timestamp': datetime.now().isoformat(),
            'state': json.loads(json.dumps(state))  # Deep copy
        }
        
        state['checkpoints'].append(checkpoint)
        await self.save_state(workflow_id, state)
        
        return checkpoint
    
    async def restore_checkpoint(self, workflow_id: str, checkpoint_name: str) -> Dict[str, Any]:
        """Restore from checkpoint."""
        state = await self.get_state(workflow_id)
        if not state:
            raise Exception(f"Workflow {workflow_id} not found")
        
        checkpoint = next(
            (cp for cp in state['checkpoints'] if cp['name'] == checkpoint_name),
            None
        )
        
        if not checkpoint:
            raise Exception(f"Checkpoint {checkpoint_name} not found")
        
        restored_state = {
            **checkpoint['state'],
            'restored_from': checkpoint_name,
            'restored_at': datetime.now().isoformat()
        }
        
        await self.save_state(workflow_id, restored_state)
        return restored_state
    
    async def get_workflow_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow state."""
        return await self.get_state(workflow_id)
    
    async def get_workflow_history(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get workflow history."""
        if workflow_id in self.state_history:
            return self.state_history[workflow_id]
        
        if self.kv_namespace:
            try:
                history_data = await self.kv_namespace.get(f"history:{workflow_id}", 'json')
                return history_data or []
            except Exception as error:
                console.error('Failed to get workflow history:', str(error))
                return []
        
        return []
    
    async def list_workflows(self, options: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """List all workflows."""
        options = options or {}
        status = options.get('status')
        limit = options.get('limit', 100)
        cursor = options.get('cursor')
        
        if self.kv_namespace:
            try:
                list_options = {
                    'prefix': 'workflow:',
                    'limit': limit
                }
                if cursor:
                    list_options['cursor'] = cursor
                
                result = await self.kv_namespace.list(list_options)
                
                workflows = []
                for key in result['keys']:
                    try:
                        state = await self.kv_namespace.get(key['name'], 'json')
                        if state:
                            workflows.append(state)
                    except Exception:
                        continue
                
                if status:
                    workflows = [w for w in workflows if w.get('status') == status]
                
                return workflows
                
            except Exception as error:
                console.error('Failed to list workflows:', str(error))
        
        # Fallback to in-memory state
        workflows = list(self.in_memory_state.values())
        if status:
            workflows = [w for w in workflows if w.get('status') == status]
        
        return workflows[:limit]
    
    async def cleanup_old_workflows(self, older_than_days: int = 7) -> int:
        """Clean up old workflows."""
        cutoff_date = datetime.now() - timedelta(days=older_than_days)
        workflows = await self.list_workflows()
        cleaned = 0
        
        for workflow in workflows:
            end_time_str = workflow.get('end_time')
            if end_time_str:
                try:
                    end_time = datetime.fromisoformat(end_time_str.replace('Z', '+00:00'))
                    if end_time < cutoff_date:
                        await self.delete_workflow(workflow['workflow_id'])
                        cleaned += 1
                except Exception:
                    continue
        
        return cleaned
    
    async def get_statistics(self) -> Dict[str, Any]:
        """Get workflow statistics."""
        workflows = await self.list_workflows()
        
        stats = {
            'total': len(workflows),
            'by_status': {},
            'average_duration': 0,
            'success_rate': 0,
            'top_errors': []
        }
        
        total_duration = 0
        completed_count = 0
        error_counts = {}
        
        for workflow in workflows:
            # Count by status
            status = workflow.get('status', 'unknown')
            stats['by_status'][status] = stats['by_status'].get(status, 0) + 1
            
            # Calculate average duration
            duration = workflow.get('duration', 0)
            if duration > 0:
                total_duration += duration
                completed_count += 1
            
            # Count errors
            errors = workflow.get('errors', [])
            for error in errors:
                error_msg = error.get('error', 'Unknown error')
                error_counts[error_msg] = error_counts.get(error_msg, 0) + 1
        
        # Calculate statistics
        if completed_count > 0:
            stats['average_duration'] = total_duration / completed_count
        
        if stats['total'] > 0:
            stats['success_rate'] = stats['by_status'].get('completed', 0) / stats['total']
        
        # Get top errors
        stats['top_errors'] = [
            {'error': error, 'count': count}
            for error, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        
        return stats
    
    async def save_state(self, workflow_id: str, state: Dict[str, Any]) -> None:
        """Save state to storage."""
        # Save to in-memory cache
        self.in_memory_state[workflow_id] = state
        
        # Track history
        if workflow_id not in self.state_history:
            self.state_history[workflow_id] = []
        
        self.state_history[workflow_id].append({
            'timestamp': datetime.now().isoformat(),
            'state': json.loads(json.dumps(state))  # Deep copy
        })
        
        # Persist to KV if available
        if self.kv_namespace:
            try:
                await self.kv_namespace.put(
                    f"workflow:{workflow_id}",
                    json.dumps(state),
                    {'expirationTtl': 86400 * 30}  # 30 days
                )
            except Exception as error:
                console.error('Failed to persist state to KV:', str(error))
    
    async def get_state(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get state from storage."""
        # Check in-memory cache first
        if workflow_id in self.in_memory_state:
            return self.in_memory_state[workflow_id]
        
        # Try to load from KV
        if self.kv_namespace:
            try:
                state_data = await self.kv_namespace.get(f"workflow:{workflow_id}", 'json')
                if state_data:
                    self.in_memory_state[workflow_id] = state_data
                    return state_data
            except Exception as error:
                console.error('Failed to load state from KV:', str(error))
        
        return None
    
    async def archive_workflow(self, workflow_id: str) -> None:
        """Archive completed workflow."""
        if self.kv_namespace:
            try:
                state = await self.get_state(workflow_id)
                history = self.state_history.get(workflow_id, [])
                
                # Save to archive
                archive_data = {'state': state, 'history': history}
                await self.kv_namespace.put(
                    f"archive:{workflow_id}",
                    json.dumps(archive_data),
                    {'expirationTtl': 86400 * 90}  # 90 days
                )
                
                # Save history separately
                await self.kv_namespace.put(
                    f"history:{workflow_id}",
                    json.dumps(history),
                    {'expirationTtl': 86400 * 90}  # 90 days
                )
            except Exception as error:
                console.error('Failed to archive workflow:', str(error))
    
    async def delete_workflow(self, workflow_id: str) -> None:
        """Delete workflow."""
        # Remove from in-memory caches
        self.in_memory_state.pop(workflow_id, None)
        self.state_history.pop(workflow_id, None)
        
        # Remove from KV if available
        if self.kv_namespace:
            try:
                await self.kv_namespace.delete(f"workflow:{workflow_id}")
                await self.kv_namespace.delete(f"archive:{workflow_id}")
                await self.kv_namespace.delete(f"history:{workflow_id}")
            except Exception as error:
                console.error('Failed to delete workflow:', str(error))
    
    def calculate_duration(self, start_time: str, end_time: str) -> int:
        """Calculate duration in milliseconds."""
        try:
            start = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            return int((end - start).total_seconds() * 1000)
        except Exception:
            return 0