"""
Base Agent for Cloudflare Workers with Pyodide Runtime
Provides core functionality for AI agents including CORS, caching, and AI calls
"""

import json
import asyncio
from typing import Dict, Any, Optional, Union, List
from urllib.parse import urlparse, parse_qs
from datetime import datetime, timedelta

# Cloudflare Workers FFI imports
from js import console, fetch, Response, Headers, URL
from js import JSON as js_json


class BaseAgent:
    """Base class for Cloudflare Workers AI agents with Pyodide runtime."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the base agent with configuration."""
        self.config = config
        
        # Agent metadata
        self.name = config.get('name', 'AI Agent')
        self.description = config.get('description', 'A helpful AI assistant')
        self.icon = config.get('icon', '🤖')
        self.subtitle = config.get('subtitle', 'Powered by Cloudflare Workers')
        self.system_prompt = config.get('system_prompt', 'You are a helpful AI assistant.')
        self.placeholder = config.get('placeholder', 'Ask me anything...')
        self.ai_label = config.get('ai_label', 'AI Assistant')
        
        # AI model configuration
        self.model = config.get('model', '@cf/meta/llama-3.1-8b-instruct')
        self.max_tokens = config.get('max_tokens', 1000)
        self.temperature = config.get('temperature', 0.7)
        
        # Caching configuration
        self.cache_enabled = config.get('cache_enabled', True)
        self.cache_ttl = config.get('cache_ttl', 3600)
        
        # CORS configuration
        self.cors_origins = config.get('cors_origins', ['*'])
        self.cors_methods = config.get('cors_methods', ['GET', 'POST', 'OPTIONS'])
        self.cors_headers = config.get('cors_headers', ['Content-Type', 'Authorization'])
        
        # Rate limiting
        self.rate_limit = config.get('rate_limit', 100)  # requests per minute
        
        # Request cache for deduplication
        self.request_cache = {}
    
    async def handle_request(self, request, env, context) -> Response:
        """Main request handler for Cloudflare Workers."""
        try:
            # Handle CORS preflight
            if request.method == 'OPTIONS':
                return self.create_cors_response()
            
            url = URL.new(request.url)
            pathname = url.pathname
            
            # Route requests
            if pathname == '/':
                return await self.handle_chat_interface(request, env)
            elif pathname == '/api/chat':
                return await self.handle_api_chat(request, env)
            elif pathname == '/api/status':
                return await self.handle_status(request, env)
            elif pathname.startswith('/api/workflow/'):
                return await self.handle_workflow_api(request, env, pathname)
            elif pathname == '/mcp':
                return await self.handle_mcp_protocol(request, env)
            else:
                return self.create_error_response('Not Found', 404)
        
        except Exception as error:
            console.error('Request handling error:', str(error))
            return self.create_error_response('Internal Server Error', 500)
    
    async def handle_chat_interface(self, request, env) -> Response:
        """Handle chat interface requests."""
        html_content = self.get_chat_interface_html()
        
        headers = Headers.new()
        headers.set('Content-Type', 'text/html; charset=utf-8')
        
        return Response.new(html_content, {
            'status': 200,
            'headers': headers
        })
    
    async def handle_api_chat(self, request, env) -> Response:
        """Handle API chat requests."""
        if request.method != 'POST':
            return self.create_error_response('Method Not Allowed', 405)
        
        try:
            body = await request.json()
            question = body.get('question', '').strip()
            
            if not question:
                return self.create_error_response('Question is required', 400)
            
            # Check cache first
            cache_key = self.get_cache_key(question)
            if self.cache_enabled and cache_key in self.request_cache:
                cached_response = self.request_cache[cache_key]
                if self.is_cache_valid(cached_response['timestamp']):
                    return self.create_json_response(cached_response['data'])
            
            # Process the question
            result = await self.process_question(env, question)
            
            # Cache the response
            if self.cache_enabled:
                self.request_cache[cache_key] = {
                    'data': result,
                    'timestamp': datetime.now()
                }
            
            return self.create_json_response(result)
            
        except Exception as error:
            console.error('API chat error:', str(error))
            return self.create_error_response(f'Processing error: {str(error)}', 500)
    
    async def handle_status(self, request, env) -> Response:
        """Handle status requests."""
        status = {
            'name': self.name,
            'description': self.description,
            'model': self.model,
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'cache_size': len(self.request_cache),
            'version': '1.0.0'
        }
        
        return self.create_json_response(status)
    
    async def handle_workflow_api(self, request, env, pathname: str) -> Response:
        """Handle workflow-specific API endpoints."""
        # Extract workflow ID from path
        path_parts = pathname.split('/')
        if len(path_parts) < 4:
            return self.create_error_response('Invalid workflow path', 400)
        
        workflow_id = path_parts[3]
        action = path_parts[4] if len(path_parts) > 4 else 'status'
        
        if action == 'status':
            try:
                status = await self.get_workflow_status(workflow_id)
                return self.create_json_response(status)
            except Exception as error:
                return self.create_error_response(f'Workflow not found: {str(error)}', 404)
        
        return self.create_error_response('Unknown workflow action', 400)
    
    async def handle_mcp_protocol(self, request, env) -> Response:
        """Handle MCP (Model Context Protocol) requests."""
        if request.method != 'POST':
            return self.create_error_response('Method Not Allowed', 405)
        
        try:
            body = await request.json()
            method = body.get('method', '')
            params = body.get('params', {})
            
            if method == 'tools/list':
                return self.create_json_response({
                    'tools': [{
                        'name': self.name,
                        'description': self.description,
                        'inputSchema': {
                            'type': 'object',
                            'properties': {
                                'question': {'type': 'string', 'description': 'The question to ask'}
                            },
                            'required': ['question']
                        }
                    }]
                })
            elif method == 'tools/call':
                question = params.get('arguments', {}).get('question', '')
                if not question:
                    return self.create_error_response('Question parameter required', 400)
                
                result = await self.process_question(env, question)
                return self.create_json_response({
                    'content': [{'type': 'text', 'text': result.get('response', '')}],
                    'isError': False
                })
            else:
                return self.create_error_response('Unknown MCP method', 400)
                
        except Exception as error:
            console.error('MCP protocol error:', str(error))
            return self.create_error_response(f'MCP error: {str(error)}', 500)
    
    async def process_question(self, env: Any, question: str) -> Dict[str, Any]:
        """Process a question (to be overridden by subclasses)."""
        response = await self.call_llm(env, question)
        
        return {
            'response': response,
            'model': self.model,
            'timestamp': datetime.now().isoformat()
        }
    
    async def call_llm(self, env: Any, prompt: str, **kwargs) -> str:
        """Call the Cloudflare AI API."""
        try:
            messages = [
                {'role': 'system', 'content': self.system_prompt},
                {'role': 'user', 'content': prompt}
            ]
            
            request_data = {
                'messages': messages,
                'max_tokens': kwargs.get('max_tokens', self.max_tokens),
                'temperature': kwargs.get('temperature', self.temperature)
            }
            
            response = await env.AI.run(self.model, request_data)
            
            if hasattr(response, 'response'):
                return response.response
            else:
                return str(response)
                
        except Exception as error:
            console.error('LLM call error:', str(error))
            raise Exception(f'AI model error: {str(error)}')
    
    def create_cors_response(self) -> Response:
        """Create CORS preflight response."""
        headers = Headers.new()
        headers.set('Access-Control-Allow-Origin', '*')
        headers.set('Access-Control-Allow-Methods', ', '.join(self.cors_methods))
        headers.set('Access-Control-Allow-Headers', ', '.join(self.cors_headers))
        headers.set('Access-Control-Max-Age', '86400')
        
        return Response.new('', {
            'status': 204,
            'headers': headers
        })
    
    def create_json_response(self, data: Any, status: int = 200) -> Response:
        """Create JSON response with CORS headers."""
        headers = Headers.new()
        headers.set('Content-Type', 'application/json')
        headers.set('Access-Control-Allow-Origin', '*')
        headers.set('Access-Control-Allow-Methods', ', '.join(self.cors_methods))
        headers.set('Access-Control-Allow-Headers', ', '.join(self.cors_headers))
        
        return Response.new(json.dumps(data), {
            'status': status,
            'headers': headers
        })
    
    def create_error_response(self, message: str, status: int = 400) -> Response:
        """Create error response with CORS headers."""
        error_data = {
            'error': message,
            'status': status,
            'timestamp': datetime.now().isoformat()
        }
        
        return self.create_json_response(error_data, status)
    
    def get_cache_key(self, question: str) -> str:
        """Generate cache key for question."""
        # Simple hash-like key generation
        return f"q_{abs(hash(question))}"
    
    def is_cache_valid(self, timestamp: datetime) -> bool:
        """Check if cached response is still valid."""
        expiry = timestamp + timedelta(seconds=self.cache_ttl)
        return datetime.now() < expiry
    
    def get_chat_interface_html(self) -> str:
        """Generate chat interface HTML."""
        # Using triple-quoted strings to avoid Jinja2 conflicts
        css_styles = """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
            width: 90%;
            max-width: 800px;
            height: 80vh;
            display: flex;
            flex-direction: column;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .header .subtitle {
            opacity: 0.9;
            font-size: 14px;
        }
        
        .chat-area {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f8f9fa;
        }
        
        .message {
            margin-bottom: 15px;
            max-width: 80%;
        }
        
        .user-message {
            margin-left: auto;
            background: #007bff;
            color: white;
            padding: 12px 16px;
            border-radius: 18px 18px 4px 18px;
        }
        
        .bot-message {
            background: white;
            padding: 12px 16px;
            border-radius: 18px 18px 18px 4px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.1);
        }
        
        .input-area {
            padding: 20px;
            border-top: 1px solid #e9ecef;
            background: white;
        }
        
        .input-container {
            display: flex;
            gap: 10px;
        }
        
        #messageInput {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e9ecef;
            border-radius: 25px;
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s;
        }
        
        #messageInput:focus {
            border-color: #007bff;
        }
        
        #sendButton {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 25px;
            cursor: pointer;
            font-weight: 500;
            transition: transform 0.2s;
        }
        
        #sendButton:hover {
            transform: translateY(-1px);
        }
        
        #sendButton:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 10px;
            color: #666;
            font-style: italic;
        }
        
        .welcome {
            text-align: center;
            color: #666;
            padding: 40px 20px;
        }
        
        .welcome-icon {
            font-size: 48px;
            margin-bottom: 16px;
        }
        """
        
        javascript_code = """
        const chatArea = document.getElementById('chatArea');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const loading = document.getElementById('loading');
        
        function addMessage(content, isUser = false) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
            messageDiv.textContent = content;
            chatArea.appendChild(messageDiv);
            chatArea.scrollTop = chatArea.scrollHeight;
        }
        
        function showLoading(show) {
            loading.style.display = show ? 'block' : 'none';
            sendButton.disabled = show;
        }
        
        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message) return;
            
            // Clear input and add user message
            messageInput.value = '';
            addMessage(message, true);
            showLoading(true);
            
            try {
                const response = await fetch('/api/chat', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ question: message })
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    addMessage(data.response || data.message || 'No response received');
                } else {
                    addMessage(`Error: ${data.error || 'Unknown error occurred'}`);
                }
            } catch (error) {
                addMessage(`Error: ${error.message}`);
            } finally {
                showLoading(false);
            }
        }
        
        sendButton.addEventListener('click', sendMessage);
        messageInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });
        
        // Focus input on load
        messageInput.focus();
        """
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.name}</title>
    <style>{css_styles}</style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{self.icon} {self.name}</h1>
            <div class="subtitle">{self.subtitle}</div>
        </div>
        
        <div class="chat-area" id="chatArea">
            <div class="welcome">
                <div class="welcome-icon">{self.icon}</div>
                <h3>Welcome to {self.name}</h3>
                <p>{self.description}</p>
            </div>
        </div>
        
        <div class="loading" id="loading">
            {self.ai_label} is thinking...
        </div>
        
        <div class="input-area">
            <div class="input-container">
                <input 
                    type="text" 
                    id="messageInput" 
                    placeholder="{self.placeholder}"
                    maxlength="1000"
                >
                <button id="sendButton">Send</button>
            </div>
        </div>
    </div>
    
    <script>{javascript_code}</script>
</body>
</html>"""