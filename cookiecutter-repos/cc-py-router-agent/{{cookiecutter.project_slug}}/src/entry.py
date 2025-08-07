"""
Auto-generated Python router agent
{{cookiecutter.project_name}}
"""

import json
from typing import Dict, Any, Optional
from js import fetch, Response, Headers, console

# Import agent framework
from agent_framework.router_agent import RouterAgent
from agent_framework.tool_registry import ToolRegistry, DynamicMCPClient


class {{cookiecutter.agent_class_name}}(RouterAgent):
    """Python-based AI router agent for intelligent question routing."""
    
    def __init__(self):
        """Initialize the router with configuration."""
        config = {
            'name': '{{cookiecutter.project_name}}',
            'description': '{{cookiecutter.description}}',
            'icon': '{{cookiecutter.icon}}',
            'subtitle': '{{cookiecutter.subtitle}}',
            'systemPrompt': '''{{cookiecutter.system_prompt}}''',
            'placeholder': '{{cookiecutter.placeholder}}',
            'examples': {{cookiecutter.examples_json}},
            'aiLabel': '{{cookiecutter.ai_label}}',
            'footer': '{{cookiecutter.footer}}',
            'model': '{{cookiecutter.ai_model}}',
            'maxTokens': {{cookiecutter.max_tokens}},
            'temperature': {{cookiecutter.temperature}},
            'cacheEnabled': {{cookiecutter.cache_enabled}},
            'cacheTTL': {{cookiecutter.cache_ttl}}
        }
        super().__init__(config)
        
        # Initialize tool registry
        registry_config = {{cookiecutter.registry_json}}
        self.registry = ToolRegistry(registry_config)
        self.mcp_client = DynamicMCPClient(self.registry)
    
    async def process_question(self, env: Any, question: str) -> Dict[str, Any]:
        """Process and route questions to appropriate specialists."""
        # Check cache first
        cache_key = f"q:{question.lower().strip()}"
        cached = await self.get_from_cache(env, cache_key)
        
        if cached:
            return {'answer': cached, 'cached': True}
        
        answer = None
        source = self.config['name']
        
        # Try to route to specialized agent
        try:
            tool_result = await self.mcp_client.ask_tool(question)
            
            if tool_result:
                answer = tool_result.get('answer')
                source = tool_result.get('source', source)
                
                # Add attribution
                answer = f"{answer}\n\n*[This response was provided by {source}]*"
        except Exception as e:
            console.error(f"Failed to contact specialized agent: {e}")
            # Fall through to local AI
        
        # If no specialized agent or it failed, use local AI
        if not answer:
            enhanced_prompt = f"""{self.config['systemPrompt']}
            
Note: You have access to specialized agents for certain topics:
{self._get_tool_summary()}
If a question is better suited for a specialized agent, mention it in your response."""
            
            # Call Cloudflare AI
            ai_response = await env.AI.run(
                self.config['model'],
                {
                    'messages': [
                        {'role': 'system', 'content': enhanced_prompt},
                        {'role': 'user', 'content': f'Question: {question}'}
                    ],
                    'max_tokens': self.config['maxTokens'],
                    'temperature': self.config['temperature']
                }
            )
            
            answer = ai_response.response or 'I apologize, but I could not generate a response. Please try again.'
        
        # Cache the response
        await self.put_in_cache(env, cache_key, answer)
        
        return {'answer': answer, 'cached': False, 'source': source}
    
    def _get_tool_summary(self) -> str:
        """Get a summary of available tools."""
        tools = self.registry.get_all_tools()
        if not tools:
            return 'No specialized agents currently available.'
        
        summaries = []
        for tool in tools:
            summaries.append(f"- {tool['name']}: {tool['description']}")
        
        return '\n'.join(summaries)


# Cloudflare Workers entry point
async def on_fetch(request, env):
    """Handle incoming requests."""
    agent = {{cookiecutter.agent_class_name}}()
    return await agent.fetch(request, env)