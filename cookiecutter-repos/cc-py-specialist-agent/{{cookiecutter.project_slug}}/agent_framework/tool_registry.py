"""
Tool Registry for dynamic agent discovery and routing
"""

import re
import json
from typing import Dict, Any, List, Optional
from js import fetch, console, Headers


class ToolRegistry:
    """Registry for managing and discovering specialist tools."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize registry with optional configuration."""
        config = config or {}
        self.tools = config.get('tools', [])
    
    def add_tool(self, tool: Dict[str, Any]) -> bool:
        """Add a new tool to the registry."""
        try:
            # Check if tool already exists
            existing = next((t for t in self.tools if t['id'] == tool['id']), None)
            if existing:
                # Update existing tool
                existing.update(tool)
            else:
                # Add new tool
                self.tools.append(tool)
            return True
        except Exception as e:
            console.error(f"Error adding tool: {e}")
            return False
    
    def remove_tool(self, tool_id: str) -> bool:
        """Remove a tool from the registry."""
        try:
            self.tools = [t for t in self.tools if t['id'] != tool_id]
            return True
        except Exception as e:
            console.error(f"Error removing tool: {e}")
            return False
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all registered tools."""
        return self.tools
    
    def find_best_tool(self, question: str) -> Optional[Dict[str, Any]]:
        """Find the best matching tool for a question."""
        if not self.tools:
            return None
        
        question_lower = question.lower()
        best_match = None
        best_score = 0
        
        for tool in self.tools:
            score = self._calculate_score(question_lower, tool)
            
            if score > best_score:
                best_score = score
                best_match = tool
        
        if best_score > 0:
            return {'tool': best_match, 'score': best_score}
        
        return None
    
    def _calculate_score(self, question: str, tool: Dict[str, Any]) -> float:
        """Calculate matching score for a tool."""
        score = 0
        
        # Check keywords (1 point each)
        keywords = tool.get('keywords', [])
        for keyword in keywords:
            if keyword.lower() in question:
                score += 1
        
        # Check patterns (2 points each)
        patterns = tool.get('patterns', [])
        for pattern in patterns:
            try:
                if re.search(pattern, question, re.IGNORECASE):
                    score += 2
            except re.error as e:
                console.error(f"Invalid regex pattern {pattern}: {e}")
        
        # Apply priority multiplier
        priority = tool.get('priority', 1)
        score *= priority
        
        return score


class DynamicMCPClient:
    """Client for making MCP protocol calls to specialist agents."""
    
    def __init__(self, registry: ToolRegistry):
        """Initialize MCP client with registry."""
        self.registry = registry
    
    async def ask_tool(self, question: str) -> Optional[Dict[str, Any]]:
        """Ask a question to the best matching tool."""
        # Find best matching tool
        result = self.registry.find_best_tool(question)
        
        if not result:
            return None
        
        tool = result['tool']
        endpoint = tool.get('endpoint')
        
        if not endpoint:
            console.error(f"Tool {tool['id']} has no endpoint")
            return None
        
        try:
            # Make MCP call to specialist
            mcp_url = f"{endpoint}/mcp"
            
            response = await fetch(
                mcp_url,
                {
                    'method': 'POST',
                    'headers': Headers.new({
                        'Content-Type': 'application/json'
                    }),
                    'body': json.dumps({
                        'method': 'tools/call',
                        'params': {
                            'name': tool.get('mcpTool', 'specialist_tool'),
                            'arguments': {
                                'question': question
                            }
                        }
                    })
                }
            )
            
            if response.ok:
                data = await response.json()
                content = data.get('content', [])
                
                if content and len(content) > 0:
                    answer = content[0].get('text', '')
                    return {
                        'answer': answer,
                        'source': tool.get('name', 'Specialist'),
                        'tool_id': tool['id']
                    }
            else:
                console.error(f"MCP call failed with status {response.status}")
                
        except Exception as e:
            console.error(f"Error calling tool {tool['id']}: {e}")
        
        return None
    
    async def list_tool_capabilities(self, tool_id: str) -> Optional[List[Dict]]:
        """List capabilities of a specific tool."""
        tool = next((t for t in self.registry.tools if t['id'] == tool_id), None)
        
        if not tool:
            return None
        
        endpoint = tool.get('endpoint')
        if not endpoint:
            return None
        
        try:
            response = await fetch(
                f"{endpoint}/mcp",
                {
                    'method': 'POST',
                    'headers': Headers.new({
                        'Content-Type': 'application/json'
                    }),
                    'body': json.dumps({
                        'method': 'tools/list'
                    })
                }
            )
            
            if response.ok:
                data = await response.json()
                return data.get('tools', [])
                
        except Exception as e:
            console.error(f"Error listing capabilities for {tool_id}: {e}")
        
        return None