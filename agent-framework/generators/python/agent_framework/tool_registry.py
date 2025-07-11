"""
Tool Registry for Dynamic Agent Discovery and Routing
Python implementation for Cloudflare Workers
"""

import re
import json
from typing import Dict, List, Optional, Any

# Import for JavaScript fetch API via FFI
from js import fetch as js_fetch, console
from pyodide.ffi import to_js


class ToolRegistry:
    """Registry for managing and routing to specialized agents"""
    
    def __init__(self, registry_data: Dict[str, Any]):
        self.tools = registry_data.get('tools', [])
        self.routing_rules = registry_data.get('routingRules', [])
    
    def register_tool(self, tool: Dict[str, Any]) -> None:
        """Register a new tool/agent"""
        self.tools.append({
            'id': tool['id'],
            'name': tool['name'],
            'description': tool['description'],
            'endpoint': tool['endpoint'],
            'mcp_tool': tool['mcpTool'],
            'keywords': tool.get('keywords', []),
            'patterns': tool.get('patterns', []),
            'priority': tool.get('priority', 0)
        })
    
    def find_tool_for_question(self, question: str) -> Optional[Dict[str, Any]]:
        """Find the best tool for a given question"""
        lower_question = question.lower()
        matches = []
        
        for tool in self.tools:
            score = 0
            
            # Check keywords
            for keyword in tool['keywords']:
                if keyword.lower() in lower_question:
                    score += 1
            
            # Check patterns (regex)
            for pattern in tool['patterns']:
                try:
                    if re.search(pattern, question, re.IGNORECASE):
                        score += 2  # Patterns are more specific, higher weight
                except re.error:
                    console.warn(f"Invalid regex pattern: {pattern}")
                    continue
            
            if score > 0:
                total_score = score + tool['priority']
                matches.append({'tool': tool, 'score': total_score})
        
        # Return highest scoring tool
        if matches:
            matches.sort(key=lambda x: x['score'], reverse=True)
            return matches[0]['tool']
        
        return None
    
    def get_all_tools(self) -> List[Dict[str, Any]]:
        """Get all registered tools"""
        return self.tools
    
    def to_dict(self) -> Dict[str, Any]:
        """Export as dictionary for storage"""
        return {
            'tools': self.tools,
            'routing_rules': self.routing_rules,
            'version': '1.0'
        }


class DynamicMCPClient:
    """MCP Client with dynamic tool support"""
    
    def __init__(self, registry: ToolRegistry):
        self.registry = registry
    
    async def ask_tool(self, question: str) -> Optional[Dict[str, Any]]:
        """Find appropriate tool and ask it the question"""
        # Find appropriate tool
        tool = self.registry.find_tool_for_question(question)
        
        if not tool:
            return None  # No specialized tool found
        
        try:
            # Prepare the MCP request
            mcp_request = {
                'method': 'tools/call',
                'params': {
                    'name': tool['mcp_tool'],
                    'arguments': {'question': question}
                }
            }
            
            # Convert to JavaScript object for fetch
            fetch_options = to_js({
                'method': 'POST',
                'headers': to_js({
                    'Content-Type': 'application/json'
                }),
                'body': json.dumps(mcp_request)
            })
            
            # Make the request using JavaScript fetch
            response = await js_fetch(f"{tool['endpoint']}/mcp", fetch_options)
            
            if not response.ok:
                raise Exception(f"MCP request failed: {response.status}")
            
            # Get the response as text and parse JSON
            response_text = await response.text()
            result = json.loads(response_text)
            
            if 'error' in result:
                raise Exception(f"MCP error: {result['error']['message']}")
            
            # Extract text content from MCP response
            if (result.get('content') and 
                len(result['content']) > 0 and 
                result['content'][0].get('type') == 'text'):
                
                return {
                    'answer': result['content'][0]['text'],
                    'source': tool['name'],
                    'tool_id': tool['id']
                }
            
            raise Exception('Unexpected response format')
            
        except Exception as e:
            console.error(f"Error calling tool {tool['id']}: {e}")
            raise e


# Default registry configuration for cybersec agents
DEFAULT_REGISTRY = {
    'tools': [
        {
            'id': 'judge',
            'name': 'Judge - Vulnerability & Compliance Expert',
            'description': 'Specialized in CVE analysis, compliance frameworks, and security assessments',
            'endpoint': 'https://judge.mindhive.tech',
            'mcpTool': 'judge_vulnerability_compliance',
            'keywords': [
                'cve', 'vulnerability', 'vulnerabilities', 'exploit', 'patch',
                'cvss', 'score', 'severity', 'critical', 'high risk',
                'zero day', '0day', 'buffer overflow', 'sql injection',
                'xss', 'cross-site', 'csrf', 'remote code execution', 'rce',
                'compliance', 'compliant', 'regulation', 'framework',
                'soc 2', 'soc2', 'iso 27001', 'iso27001', 'nist',
                'gdpr', 'hipaa', 'pci-dss', 'pci dss', 'pcidss',
                'audit', 'control', 'requirement', 'certification',
                'sox', 'sarbanes', 'fedramp', 'ccpa', 'privacy'
            ],
            'patterns': [
                r'CVE-\d{4}-\d+',
                r'\b(SOC\s*2|GDPR|HIPAA|PCI[- ]?DSS)\b',
                r'compliance.*(requirement|audit|framework)'
            ],
            'priority': 10
        }
    ],
    'routing_rules': [
        {
            'name': 'vulnerability-first',
            'description': 'Route vulnerability questions to Judge first',
            'condition': 'contains_keyword',
            'keywords': ['vulnerability', 'cve'],
            'action': 'route_to_tool',
            'tool_id': 'judge'
        }
    ]
}