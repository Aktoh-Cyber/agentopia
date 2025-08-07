"""
Router Agent class for intelligent question routing
"""

from typing import Dict, Any, Optional
from .base_agent import BaseAgent
from js import console


class RouterAgent(BaseAgent):
    """Router agent that directs questions to appropriate specialists."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize router agent."""
        super().__init__(config)
        self.registry = None  # Set by subclass
        self.mcp_client = None  # Set by subclass
    
    async def handle_admin_request(self, request: Any, env: Any) -> Any:
        """Handle admin requests for dynamic tool registration."""
        try:
            method = request.method
            
            if method == 'POST':
                # Add new tool
                body = await request.json()
                tool = body.get('tool')
                
                if not tool:
                    return self._error_response('No tool provided', 400)
                
                success = self.registry.add_tool(tool)
                if success:
                    return self._json_response({
                        'success': True,
                        'message': f"Tool {tool.get('id')} registered successfully"
                    })
                else:
                    return self._error_response('Failed to register tool', 500)
            
            elif method == 'DELETE':
                # Remove tool
                body = await request.json()
                tool_id = body.get('toolId')
                
                if not tool_id:
                    return self._error_response('No toolId provided', 400)
                
                success = self.registry.remove_tool(tool_id)
                if success:
                    return self._json_response({
                        'success': True,
                        'message': f"Tool {tool_id} removed successfully"
                    })
                else:
                    return self._error_response('Tool not found', 404)
            
            elif method == 'GET':
                # List all tools
                tools = self.registry.get_all_tools()
                return self._json_response({'tools': tools})
            
            else:
                return self._error_response('Method not allowed', 405)
                
        except Exception as e:
            console.error(f"Admin request error: {e}")
            return self._error_response(str(e), 500)
    
    def get_routing_info(self, question: str) -> Dict[str, Any]:
        """Get routing information for a question."""
        if not self.registry:
            return {'tool': None, 'score': 0, 'reason': 'No registry configured'}
        
        # Find best matching tool
        best_tool = self.registry.find_best_tool(question)
        
        if best_tool:
            return {
                'tool': best_tool['tool'],
                'score': best_tool['score'],
                'reason': f"Matched with score {best_tool['score']}"
            }
        
        return {'tool': None, 'score': 0, 'reason': 'No matching specialist found'}