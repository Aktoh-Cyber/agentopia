"""
Auto-generated Python specialist agent
{{cookiecutter.project_name}}
"""

import json
import re
from typing import Dict, Any, Optional, List
from js import Response, Headers, console

# Import agent framework
from agent_framework.base_agent import BaseAgent


class {{cookiecutter.agent_class_name}}(BaseAgent):
    """Python-based specialized AI agent for domain-specific questions."""
    
    def __init__(self):
        """Initialize the specialist with configuration."""
        config = {
            'name': '{{cookiecutter.project_name}}',
            'description': '{{cookiecutter.description}}',
            'icon': '{{cookiecutter.icon}}',
            'subtitle': '{{cookiecutter.subtitle}}',
            'systemPrompt': '''{{cookiecutter.system_prompt}}

You are specialized in: {{cookiecutter.expertise}}

Focus your responses on your area of expertise and provide detailed, accurate information.''',
            'placeholder': '{{cookiecutter.placeholder}}',
            'examples': {{cookiecutter.examples_json}},
            'aiLabel': '{{cookiecutter.ai_label}}',
            'footer': '{{cookiecutter.footer}}',
            'model': '{{cookiecutter.ai_model}}',
            'maxTokens': {{cookiecutter.max_tokens}},
            'temperature': {{cookiecutter.temperature}},
            'cacheEnabled': {{cookiecutter.cache_enabled}},
            'cacheTTL': {{cookiecutter.cache_ttl}},
            
            # Specialist configuration
            'mcpToolName': '{{cookiecutter.mcp_tool_name}}',
            'expertise': '{{cookiecutter.expertise}}',
            'keywords': {{cookiecutter.keywords_json}},
            'patterns': {{cookiecutter.patterns_json}},
            'priority': {{cookiecutter.priority}}
        }
        super().__init__(config)
    
    async def process_question(self, env: Any, question: str) -> Dict[str, Any]:
        """Process questions with domain expertise checking."""
        # Check if this question matches our expertise
        is_relevant = self.is_question_relevant(question)
        
        if not is_relevant:
            return {
                'answer': f"This question appears to be outside my area of expertise ({self.config['expertise']}). I recommend consulting a more appropriate specialist.",
                'cached': False,
                'relevant': False
            }
        
        # Check cache first
        cache_key = f"q:{question.lower().strip()}"
        cached = await self.get_from_cache(env, cache_key)
        
        if cached:
            return {'answer': cached, 'cached': True, 'relevant': True}
        
        # Generate specialized response
        enhanced_prompt = f"""{self.config['systemPrompt']}
        
As a specialist in {self.config['expertise']}, provide a detailed and authoritative response to the following question."""
        
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
        
        return {'answer': answer, 'cached': False, 'relevant': True}
    
    def is_question_relevant(self, question: str) -> bool:
        """Check if a question is relevant to our expertise."""
        question_lower = question.lower()
        
        # Check keywords
        for keyword in self.config['keywords']:
            if keyword.lower() in question_lower:
                return True
        
        # Check patterns
        for pattern in self.config['patterns']:
            try:
                if re.search(pattern, question, re.IGNORECASE):
                    return True
            except re.error as e:
                console.error(f"Invalid regex pattern {pattern}: {e}")
        
        return False
    
    async def handle_mcp_request(self, request: Any, env: Any) -> Any:
        """Handle MCP protocol requests for this specialist."""
        try:
            body = await request.json()
            method = body.get('method')
            
            if method == 'tools/list':
                return self._json_response({
                    'tools': [{
                        'name': self.config['mcpToolName'],
                        'description': self.config['description'],
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'question': {
                                    'type': 'string',
                                    'description': 'The question to ask the specialist'
                                }
                            },
                            'required': ['question']
                        }
                    }]
                })
            
            elif method == 'tools/call':
                params = body.get('params', {})
                if params.get('name') == self.config['mcpToolName']:
                    question = params.get('arguments', {}).get('question')
                    result = await self.process_question(env, question)
                    
                    return self._json_response({
                        'content': [{
                            'type': 'text',
                            'text': result['answer']
                        }],
                        'metadata': {
                            'cached': result.get('cached', False),
                            'relevant': result.get('relevant', True),
                            'source': self.config['name'],
                            'expertise': self.config['expertise']
                        }
                    })
            
            return self._error_response('Method not found', 404)
            
        except Exception as e:
            console.error(f"MCP request error: {e}")
            return self._error_response(str(e), 500)


# Cloudflare Workers entry point
async def on_fetch(request, env):
    """Handle incoming requests."""
    agent = {{cookiecutter.agent_class_name}}()
    return await agent.fetch(request, env)