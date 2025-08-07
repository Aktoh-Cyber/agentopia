"""
Base Agent class for Cloudflare Workers Python Runtime
"""

import json
from typing import Dict, Any, Optional, List
from js import Response, Headers, console, fetch


class BaseAgent:
    """Base class for all agents with common functionality."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize base agent with configuration."""
        self.config = config
        self.cors_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Content-Type': 'application/json'
        }
    
    async def fetch(self, request: Any, env: Any) -> Any:
        """Main request handler."""
        url = request.url
        method = request.method
        
        # Handle CORS preflight
        if method == 'OPTIONS':
            return self._cors_response('')
        
        # Route based on path
        if '/mcp' in url:
            return await self.handle_mcp_request(request, env)
        elif '/admin/tools' in url:
            return await self.handle_admin_request(request, env)
        elif method == 'POST':
            return await self.handle_question(request, env)
        else:
            return await self.handle_ui_request()
    
    async def handle_question(self, request: Any, env: Any) -> Any:
        """Handle question requests."""
        try:
            body = await request.json()
            question = body.get('question', '')
            
            if not question:
                return self._error_response('No question provided', 400)
            
            result = await self.process_question(env, question)
            return self._json_response(result)
            
        except Exception as e:
            console.error(f"Error processing question: {e}")
            return self._error_response(str(e), 500)
    
    async def process_question(self, env: Any, question: str) -> Dict[str, Any]:
        """Process a question - to be overridden by subclasses."""
        # Check cache first
        cache_key = f"q:{question.lower().strip()}"
        cached = await self.get_from_cache(env, cache_key)
        
        if cached:
            return {'answer': cached, 'cached': True}
        
        # Generate response using AI
        response = await env.AI.run(
            self.config.get('model', '@cf/meta/llama-3.1-70b-instruct'),
            {
                'messages': [
                    {'role': 'system', 'content': self.config.get('systemPrompt', '')},
                    {'role': 'user', 'content': f'Question: {question}'}
                ],
                'max_tokens': self.config.get('maxTokens', 1000),
                'temperature': self.config.get('temperature', 0.7)
            }
        )
        
        answer = response.response or 'I apologize, but I could not generate a response.'
        
        # Cache the response
        await self.put_in_cache(env, cache_key, answer)
        
        return {'answer': answer, 'cached': False}
    
    async def handle_mcp_request(self, request: Any, env: Any) -> Any:
        """Handle MCP protocol requests."""
        try:
            body = await request.json()
            method = body.get('method')
            
            if method == 'tools/list':
                return self._json_response({
                    'tools': [{
                        'name': self.config.get('mcpToolName', 'agent_tool'),
                        'description': self.config.get('description', ''),
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'question': {
                                    'type': 'string',
                                    'description': 'The question to ask'
                                }
                            },
                            'required': ['question']
                        }
                    }]
                })
            
            elif method == 'tools/call':
                params = body.get('params', {})
                if params.get('name') == self.config.get('mcpToolName', 'agent_tool'):
                    question = params.get('arguments', {}).get('question')
                    result = await self.process_question(env, question)
                    
                    return self._json_response({
                        'content': [{
                            'type': 'text',
                            'text': result['answer']
                        }],
                        'metadata': {
                            'cached': result.get('cached', False),
                            'source': self.config.get('name', 'Unknown Agent')
                        }
                    })
            
            return self._error_response('Method not found', 404)
            
        except Exception as e:
            console.error(f"MCP request error: {e}")
            return self._error_response(str(e), 500)
    
    async def handle_admin_request(self, request: Any, env: Any) -> Any:
        """Handle admin requests for tool management."""
        return self._error_response('Admin endpoint not implemented', 501)
    
    async def handle_ui_request(self) -> Any:
        """Return the UI HTML."""
        html = self._generate_ui_html()
        return Response.new(html, {
            'headers': {
                'Content-Type': 'text/html',
                'Cache-Control': 'public, max-age=3600'
            }
        })
    
    async def get_from_cache(self, env: Any, key: str) -> Optional[str]:
        """Get value from cache."""
        if not self.config.get('cacheEnabled', True):
            return None
        
        try:
            if hasattr(env, 'CACHE'):
                value = await env.CACHE.get(key)
                return value
        except Exception as e:
            console.error(f"Cache get error: {e}")
        
        return None
    
    async def put_in_cache(self, env: Any, key: str, value: str) -> None:
        """Put value in cache."""
        if not self.config.get('cacheEnabled', True):
            return
        
        try:
            if hasattr(env, 'CACHE'):
                ttl = self.config.get('cacheTTL', 3600)
                await env.CACHE.put(key, value, {'expirationTtl': ttl})
        except Exception as e:
            console.error(f"Cache put error: {e}")
    
    def _json_response(self, data: Any) -> Any:
        """Create JSON response with CORS headers."""
        return Response.new(
            json.dumps(data),
            {'headers': self.cors_headers}
        )
    
    def _error_response(self, message: str, status: int) -> Any:
        """Create error response."""
        return Response.new(
            json.dumps({'error': message}),
            {
                'status': status,
                'headers': self.cors_headers
            }
        )
    
    def _cors_response(self, body: str) -> Any:
        """Create CORS response."""
        return Response.new(body, {'headers': self.cors_headers})
    
    def _generate_ui_html(self) -> str:
        """Generate the UI HTML."""
        return f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.config.get('name', 'AI Agent')}</title>
    <style>
        /* Styles omitted for brevity - same as JavaScript version */
    </style>
</head>
<body>
    <div class="container">
        <header>
            <span class="icon">{self.config.get('icon', '🤖')}</span>
            <h1>{self.config.get('name', 'AI Agent')}</h1>
            <p class="subtitle">{self.config.get('subtitle', '')}</p>
        </header>
        <!-- Chat interface HTML -->
    </div>
    <script>
        // JavaScript code for chat interface
    </script>
</body>
</html>'''