"""
Base Agent Class - Common functionality for all Python agents
Now includes LangChain-style interface for familiar development patterns
Designed to work with Cloudflare Workers Python runtime
"""

import json
from typing import Any, Optional, List, Dict
from urllib.parse import urlparse

# For accessing JavaScript APIs via FFI
from js import console
from pyodide.ffi import to_js

# Import Workers-specific modules
from workers import Response

# Import our LangChain-compatible interfaces
try:
    from .langchain_compat import (
        BaseMessage, SystemMessage, HumanMessage, AIMessage,
        ChatPromptTemplate, PromptTemplate,
        BaseLLM, LLMChain,
        ConversationBufferMemory,
        StrOutputParser, JsonOutputParser
    )
    LANGCHAIN_COMPAT_AVAILABLE = True
except ImportError:
    LANGCHAIN_COMPAT_AVAILABLE = False


class CloudflareWorkersLLM(BaseLLM if LANGCHAIN_COMPAT_AVAILABLE else object):
    """LLM implementation for Cloudflare Workers"""
    
    def __init__(self, env, model: str, temperature: float = 0.3, max_tokens: int = 512):
        self.env = env
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
    
    async def agenerate(self, messages: List[BaseMessage], **kwargs: Any) -> str:
        """Generate response using Cloudflare AI"""
        try:
            # Convert messages to format expected by Cloudflare AI
            cf_messages = []
            for msg in messages:
                cf_messages.append({
                    "role": msg.role,
                    "content": msg.content
                })
            
            # Convert to JavaScript format
            js_messages = to_js(cf_messages)
            ai_params = to_js({
                "messages": js_messages,
                "max_tokens": kwargs.get("max_tokens", self.max_tokens),
                "temperature": kwargs.get("temperature", self.temperature),
            })
            
            response = await self.env.AI.run(self.model, ai_params)
            return (
                response.response
                or "I apologize, but I could not generate a response. Please try again."
            )
        except Exception as e:
            console.error(f"AI call error: {e}")
            return "I apologize, but I encountered an error. Please try again."


class BaseAgent:
    """Base class providing common functionality for all agents with optional LangChain-style interface"""

    def __init__(self, config: dict[str, Any]):
        self.config = {
            "name": config.get("name", "AI Agent"),
            "description": config.get("description", "An AI assistant"),
            "icon": config.get("icon", "🤖"),
            "subtitle": config.get("subtitle", "Powered by AI"),
            "system_prompt": config.get("systemPrompt", "You are a helpful AI assistant."),
            "examples": config.get("examples", []),
            "max_tokens": config.get("maxTokens", 512),
            "temperature": config.get("temperature", 0.3),
            "model": config.get("model", "@cf/meta/llama-3.1-8b-instruct"),
            "cache_enabled": config.get("cacheEnabled", True),
            "cache_ttl": config.get("cacheTTL", 3600),
            "placeholder": config.get("placeholder", "Ask a question..."),
            "ai_label": config.get("aiLabel", "AI Assistant"),
            "footer": config.get("footer", "Built with Cloudflare Workers AI"),
            "mcp_tool_name": config.get(
                "mcpToolName", f"{config.get('name', 'agent').lower().replace(' ', '_')}_tool"
            ),
            "use_langchain": config.get("useLangchain", True),  # Enable LangChain by default
            **config,
        }
        
        # Initialize LangChain-style components if available and enabled
        if LANGCHAIN_COMPAT_AVAILABLE and self.config["use_langchain"]:
            self.memory = ConversationBufferMemory(return_messages=True)
            self.output_parser = StrOutputParser()
            self.llm: Optional[CloudflareWorkersLLM] = None
            self.chain: Optional[LLMChain] = None
            self.prompt_template: Optional[ChatPromptTemplate] = None
        else:
            self.memory = None
            self.output_parser = None
            self.llm = None
            self.chain = None
            self.prompt_template = None
    
    def setup_langchain_components(self, env):
        """Initialize LangChain components with environment"""
        if not LANGCHAIN_COMPAT_AVAILABLE or not self.config["use_langchain"]:
            return
        
        # Initialize LLM
        self.llm = CloudflareWorkersLLM(
            env=env,
            model=self.config["model"],
            temperature=self.config["temperature"],
            max_tokens=self.config["max_tokens"]
        )
        
        # Create prompt template
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.config["system_prompt"]),
            ("human", "{question}")
        ])
        
        # Create chain
        self.chain = LLMChain(llm=self.llm, prompt=self.prompt_template)

    def get_cors_headers(self) -> dict[str, str]:
        """Standard CORS headers"""
        return {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }

    def handle_options(self) -> Response:
        """Handle preflight requests"""
        return Response("", headers=self.get_cors_headers())

    async def get_from_cache(self, env, key: str) -> Optional[str]:
        """Get from cache if enabled"""
        if not self.config["cache_enabled"] or not hasattr(env, "CACHE"):
            return None
        try:
            return await env.CACHE.get(key)
        except Exception as e:
            console.error(f"Cache get error: {e}")
            return None

    async def put_in_cache(self, env, key: str, value: str) -> None:
        """Put in cache if enabled"""
        if not self.config["cache_enabled"] or not hasattr(env, "CACHE"):
            return
        try:
            await env.CACHE.put(key, value, expirationTtl=self.config["cache_ttl"])
        except Exception as e:
            console.error(f"Cache put error: {e}")

    async def call_ai(self, env, question: str) -> str:
        """Call AI model with system prompt (legacy method)"""
        try:
            # Convert Python data to JavaScript format for the AI call
            messages = to_js(
                [
                    {"role": "system", "content": self.config["system_prompt"]},
                    {"role": "user", "content": f"Question: {question}"},
                ]
            )

            ai_params = to_js(
                {
                    "messages": messages,
                    "max_tokens": self.config["max_tokens"],
                    "temperature": self.config["temperature"],
                }
            )

            response = await env.AI.run(self.config["model"], ai_params)
            return (
                response.response
                or "I apologize, but I could not generate a response. Please try again."
            )
        except Exception as e:
            console.error(f"AI call error: {e}")
            return "I apologize, but I encountered an error. Please try again."

    async def process_question_langchain(self, env, question: str) -> dict[str, Any]:
        """Process a question using LangChain-style components"""
        # Initialize components if not already done
        if self.llm is None:
            self.setup_langchain_components(env)
        
        # Check cache first
        cache_key = f"q:{question.lower().strip()}"
        cached = await self.get_from_cache(env, cache_key)
        
        if cached:
            return {"answer": cached, "cached": True}
        
        # Add to memory
        self.memory.add_user_message(question)
        
        # Run chain
        try:
            answer = await self.chain.arun(question=question)
            
            # Parse output if needed
            parsed_answer = self.output_parser.parse(answer)
            
            # Add AI response to memory
            self.memory.add_ai_message(parsed_answer)
            
            # Cache the response
            await self.put_in_cache(env, cache_key, parsed_answer)
            
            return {"answer": parsed_answer, "cached": False}
        except Exception as e:
            console.error(f"Error processing question: {e}")
            error_msg = "I apologize, but I encountered an error processing your question."
            self.memory.add_ai_message(error_msg)
            return {"answer": error_msg, "cached": False}

    async def process_question_legacy(self, env, question: str) -> dict[str, Any]:
        """Process a question (legacy method)"""
        # Check cache first
        cache_key = f"q:{question.lower().strip()}"
        cached = await self.get_from_cache(env, cache_key)

        if cached:
            return {"answer": cached, "cached": True}

        # Get AI response
        answer = await self.call_ai(env, question)

        # Cache the response
        await self.put_in_cache(env, cache_key, answer)

        return {"answer": answer, "cached": False}

    async def process_question(self, env, question: str) -> dict[str, Any]:
        """Process a question (uses LangChain style if available and enabled)"""
        if LANGCHAIN_COMPAT_AVAILABLE and self.config["use_langchain"]:
            return await self.process_question_langchain(env, question)
        else:
            return await self.process_question_legacy(env, question)

    def handle_mcp_tools_list(self) -> dict[str, Any]:
        """Handle MCP tools/list request"""
        return {
            "tools": [
                {
                    "name": self.config["mcp_tool_name"],
                    "description": self.config["description"],
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "Question to ask the agent",
                            }
                        },
                        "required": ["question"],
                    },
                }
            ]
        }

    async def handle_mcp_tool_call(self, env, params: dict[str, Any]) -> dict[str, Any]:
        """Handle MCP tools/call request"""
        question = params.get("arguments", {}).get("question")

        if not question:
            return {"error": {"code": -32602, "message": "Invalid params: question is required"}}

        result = await self.process_question(env, question)

        return {"content": [{"type": "text", "text": result["answer"]}]}

    async def handle_mcp_request(self, env, request_data: dict[str, Any]) -> dict[str, Any]:
        """Handle MCP requests"""
        method = request_data.get("method")

        if method == "tools/list":
            return self.handle_mcp_tools_list()

        if method == "tools/call":
            tool_name = request_data.get("params", {}).get("name")
            if tool_name == self.config["mcp_tool_name"]:
                return await self.handle_mcp_tool_call(env, request_data.get("params", {}))

        return {"error": {"code": -32601, "message": "Method not found"}}

    def get_home_page(self) -> str:
        """Get HTML page template"""
        examples_html = "\n                    ".join(
            f"<li>{ex}</li>" for ex in self.config["examples"]
        )

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.config['name']} - {self.config['subtitle']}</title>
    {self.get_styles()}
</head>
<body>
    <header>
        <h1>{self.config['icon']} {self.config['name']}</h1>
        <p class="subtitle">{self.config['subtitle']}</p>
    </header>

    <div class="container">
        <div class="chat-box">
            <div class="input-group">
                <input
                    type="text"
                    id="questionInput"
                    placeholder="{self.config['placeholder']}"
                    autofocus
                />
                <button id="askButton" onclick="askQuestion()">Ask</button>
            </div>

            <div id="messages" class="messages"></div>

            <div class="examples">
                <h3>Example Questions:</h3>
                <ul>
                    {examples_html}
                </ul>
            </div>
        </div>
    </div>

    <footer>
        <p>{self.config['footer']}</p>
    </footer>

    {self.get_client_script()}
</body>
</html>"""

    def get_styles(self) -> str:
        """Get CSS styles"""
        return """<style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0e27;
            color: #e0e6ed;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            background: #1a1f3a;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }

        h1 {
            text-align: center;
            color: #00d4ff;
            font-size: 2rem;
        }

        .subtitle {
            text-align: center;
            color: #8892b0;
            margin-top: 0.5rem;
        }

        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            flex: 1;
        }

        .chat-box {
            background: #1a1f3a;
            border-radius: 10px;
            padding: 2rem;
            margin-top: 2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }

        .input-group {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
        }

        input {
            flex: 1;
            padding: 1rem;
            border: 2px solid #2a3f5f;
            background: #0a0e27;
            color: #e0e6ed;
            border-radius: 5px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }

        input:focus {
            outline: none;
            border-color: #00d4ff;
        }

        button {
            padding: 1rem 2rem;
            background: #00d4ff;
            color: #0a0e27;
            border: none;
            border-radius: 5px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: background 0.3s;
        }

        button:hover {
            background: #00a8cc;
        }

        button:disabled {
            background: #2a3f5f;
            cursor: not-allowed;
        }

        .messages {
            max-height: 400px;
            overflow-y: auto;
            padding-right: 1rem;
        }

        .message {
            margin-bottom: 1.5rem;
            padding: 1rem;
            border-radius: 8px;
            animation: fadeIn 0.3s ease-in;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .user-message {
            background: #2a3f5f;
            border-left: 3px solid #00d4ff;
        }

        .ai-message {
            background: #0f1729;
            border-left: 3px solid #64ffda;
        }

        .message-label {
            font-weight: bold;
            margin-bottom: 0.5rem;
            color: #64ffda;
        }

        .user-message .message-label {
            color: #00d4ff;
        }

        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #2a3f5f;
            border-radius: 50%;
            border-top-color: #00d4ff;
            animation: spin 1s ease-in-out infinite;
        }

        @keyframes spin {
            to { transform: rotate(360deg); }
        }

        .examples {
            margin-top: 2rem;
            padding: 1rem;
            background: rgba(100, 255, 218, 0.05);
            border-radius: 8px;
        }

        .examples h3 {
            color: #64ffda;
            margin-bottom: 1rem;
        }

        .examples ul {
            list-style: none;
            padding-left: 0;
        }

        .examples li {
            margin-bottom: 0.5rem;
            padding-left: 1.5rem;
            position: relative;
        }

        .examples li:before {
            content: "▸";
            position: absolute;
            left: 0;
            color: #64ffda;
        }

        footer {
            text-align: center;
            padding: 2rem;
            color: #8892b0;
            background: #1a1f3a;
        }

        a {
            color: #00d4ff;
            text-decoration: none;
        }

        a:hover {
            text-decoration: underline;
        }
    </style>"""

    def get_client_script(self) -> str:
        """Get client-side JavaScript"""
        return f"""<script>
        const messagesDiv = document.getElementById('messages');
        const questionInput = document.getElementById('questionInput');
        const askButton = document.getElementById('askButton');

        questionInput.addEventListener('keypress', (e) => {{
            if (e.key === 'Enter' && !e.shiftKey) {{
                e.preventDefault();
                askQuestion();
            }}
        }});

        async function askQuestion() {{
            const question = questionInput.value.trim();
            if (!question) return;

            // Disable input
            questionInput.disabled = true;
            askButton.disabled = true;

            // Add user message
            addMessage(question, 'user');

            // Clear input
            questionInput.value = '';

            // Add loading message
            const loadingId = 'loading-' + Date.now();
            addMessage('<div class="loading"></div> Thinking...', 'ai', loadingId);

            try {{
                const response = await fetch('/api/ask', {{
                    method: 'POST',
                    headers: {{
                        'Content-Type': 'application/json',
                    }},
                    body: JSON.stringify({{ question }}),
                }});

                const data = await response.json();

                // Remove loading message
                document.getElementById(loadingId)?.remove();

                if (response.ok) {{
                    addMessage(data.answer, 'ai');
                }} else {{
                    addMessage('Error: ' + (data.error || 'Something went wrong'), 'ai');
                }}
            }} catch (error) {{
                // Remove loading message
                document.getElementById(loadingId)?.remove();
                addMessage('Error: Could not connect to the server', 'ai');
            }}

            // Re-enable input
            questionInput.disabled = false;
            askButton.disabled = false;
            questionInput.focus();
        }}

        function addMessage(content, type, id) {{
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + type + '-message';
            if (id) messageDiv.id = id;

            const label = document.createElement('div');
            label.className = 'message-label';
            label.textContent = type === 'user' ? 'You:' : '{self.config["ai_label"]}:';

            const contentDiv = document.createElement('div');
            contentDiv.innerHTML = content;

            messageDiv.appendChild(label);
            messageDiv.appendChild(contentDiv);

            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }}
    </script>"""

    async def fetch(self, request, env):
        """Main request handler"""
        # Parse URL and method
        url = urlparse(request.url)
        method = request.method
        cors_headers = self.get_cors_headers()

        # Handle preflight requests
        if method == "OPTIONS":
            return self.handle_options()

        # Serve homepage
        if method == "GET" and url.path == "/":
            return Response(
                self.get_home_page(), headers={"Content-Type": "text/html", **cors_headers}
            )

        # Handle MCP requests
        if method == "POST" and url.path == "/mcp":
            try:
                request_data = await request.json()
                result = await self.handle_mcp_request(env, request_data)
                return Response(
                    json.dumps(result), headers={"Content-Type": "application/json", **cors_headers}
                )
            except Exception as e:
                console.error(f"Error processing MCP request: {e}")
                error_response = {"error": {"code": -32603, "message": "Internal error"}}
                return Response(
                    json.dumps(error_response),
                    status=500,
                    headers={"Content-Type": "application/json", **cors_headers},
                )

        # Handle API requests
        if method == "POST" and url.path == "/api/ask":
            try:
                request_data = await request.json()
                question = request_data.get("question", "").strip()

                if not question:
                    return Response(
                        json.dumps({"error": "Question is required"}),
                        status=400,
                        headers={"Content-Type": "application/json", **cors_headers},
                    )

                result = await self.process_question(env, question)

                return Response(
                    json.dumps(result), headers={"Content-Type": "application/json", **cors_headers}
                )

            except Exception as e:
                console.error(f"Error processing request: {e}")
                return Response(
                    json.dumps({"error": "An error occurred processing your request"}),
                    status=500,
                    headers={"Content-Type": "application/json", **cors_headers},
                )

        # Return 404 for unhandled routes
        return Response("Not Found", status=404)