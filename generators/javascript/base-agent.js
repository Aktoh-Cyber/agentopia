/**
 * Base Agent Class - Common functionality for all agents with LangChain.js integration
 *
 * Updated for langchain 1.x compatibility - uses direct prompts instead of deprecated
 * LLMChain and BufferMemory (which have been removed in langchain 1.x)
 */

import { ChatPromptTemplate } from "@langchain/core/prompts";
import { HumanMessage, SystemMessage, AIMessage } from "@langchain/core/messages";
import { BaseLLM } from "@langchain/core/language_models/llms";

/**
 * Simple in-memory buffer for conversation history
 * Replaces deprecated BufferMemory from langchain
 */
class SimpleMemory {
  constructor(maxMessages = 10) {
    this.messages = [];
    this.maxMessages = maxMessages;
  }

  addMessage(role, content) {
    this.messages.push({ role, content, timestamp: Date.now() });
    // Keep only the last N messages
    if (this.messages.length > this.maxMessages) {
      this.messages = this.messages.slice(-this.maxMessages);
    }
  }

  getHistory() {
    return this.messages;
  }

  clear() {
    this.messages = [];
  }
}

/**
 * Custom LLM for Cloudflare Workers AI
 */
class CloudflareWorkersLLM extends BaseLLM {
  constructor(env, config) {
    super({});
    this.env = env;
    this.model = config.model;
    this.maxTokens = config.maxTokens;
    this.temperature = config.temperature;
  }

  async _call(prompt, options) {
    const response = await this.env.AI.run(this.model, {
      messages: [{ role: 'user', content: prompt }],
      max_tokens: this.maxTokens,
      temperature: this.temperature,
      ...options
    });

    return response.response || 'I apologize, but I could not generate a response. Please try again.';
  }

  async _generate(messages, options) {
    // Convert LangChain messages to Cloudflare format
    const cfMessages = messages.map(msg => {
      if (msg instanceof SystemMessage) {
        return { role: 'system', content: msg.content };
      } else if (msg instanceof HumanMessage) {
        return { role: 'user', content: msg.content };
      } else if (msg instanceof AIMessage) {
        return { role: 'assistant', content: msg.content };
      }
      return { role: 'user', content: msg.content };
    });

    const response = await this.env.AI.run(this.model, {
      messages: cfMessages,
      max_tokens: this.maxTokens,
      temperature: this.temperature,
      ...options
    });

    const text = response.response || 'I apologize, but I could not generate a response. Please try again.';
    
    return {
      generations: [{
        text,
        message: new AIMessage(text)
      }]
    };
  }

  _llmType() {
    return 'cloudflare-workers';
  }
}

export class BaseAgent {
  constructor(config) {
    this.config = {
      name: config.name || 'AI Agent',
      description: config.description || 'An AI assistant',
      icon: config.icon || '🤖',
      systemPrompt: config.systemPrompt || 'You are a helpful AI assistant.',
      examples: config.examples || [],
      maxTokens: config.maxTokens || 512,
      temperature: config.temperature || 0.3,
      model: config.model || '@cf/meta/llama-3.1-8b-instruct',
      cacheEnabled: config.cacheEnabled !== false,
      cacheTTL: config.cacheTTL || 3600,
      useLangchain: config.useLangchain !== false, // Enable LangChain by default
      ...config
    };

    // Initialize LangChain components (will be set up when env is available)
    this.llm = null;
    this.memory = null;
    this.chain = null;
    this.promptTemplate = null;
  }

  /**
   * Initialize LangChain components with environment
   * Updated for langchain 1.x - uses SimpleMemory and direct prompts
   */
  setupLangChainComponents(env) {
    if (!this.config.useLangchain) {
      return;
    }

    // Initialize LLM
    this.llm = new CloudflareWorkersLLM(env, this.config);

    // Initialize simple memory (replaces deprecated BufferMemory)
    this.memory = new SimpleMemory(10);

    // Create prompt template
    this.promptTemplate = ChatPromptTemplate.fromMessages([
      ["system", this.config.systemPrompt],
      ["human", "{question}"]
    ]);
  }

  /**
   * Standard CORS headers
   */
  getCorsHeaders() {
    return {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };
  }

  /**
   * Handle preflight requests
   */
  handleOptions() {
    return new Response(null, { headers: this.getCorsHeaders() });
  }

  /**
   * Get from cache
   */
  async getFromCache(env, key) {
    if (!this.config.cacheEnabled || !env.CACHE) {
      return null;
    }
    return await env.CACHE.get(key);
  }

  /**
   * Put in cache
   */
  async putInCache(env, key, value) {
    if (!this.config.cacheEnabled || !env.CACHE) {
      return;
    }
    await env.CACHE.put(key, value, { 
      expirationTtl: this.config.cacheTTL 
    });
  }

  /**
   * Call AI model with system prompt (legacy method)
   */
  async callAI(env, question) {
    const response = await env.AI.run(this.config.model, {
      messages: [
        { role: 'system', content: this.config.systemPrompt },
        { role: 'user', content: `Question: ${question}` }
      ],
      max_tokens: this.config.maxTokens,
      temperature: this.config.temperature,
    });

    return response.response || 'I apologize, but I could not generate a response. Please try again.';
  }

  /**
   * Process question using LangChain
   * Updated for langchain 1.x - uses direct LLM invocation instead of deprecated LLMChain
   */
  async processQuestionLangChain(env, question) {
    // Initialize components if not already done
    if (!this.llm) {
      this.setupLangChainComponents(env);
    }

    // Check cache first
    const cacheKey = `q:${question.toLowerCase().trim()}`;
    const cached = await this.getFromCache(env, cacheKey);

    if (cached) {
      return { answer: cached, cached: true };
    }

    try {
      // Format the prompt with the question
      const formattedPrompt = await this.promptTemplate.format({ question });

      // Call the LLM directly (replaces deprecated chain.call())
      const answer = await this.llm._call(formattedPrompt);

      // Store in memory for conversation context
      this.memory.addMessage('user', question);
      this.memory.addMessage('assistant', answer);

      // Cache the response
      await this.putInCache(env, cacheKey, answer);

      return { answer, cached: false };
    } catch (error) {
      console.error('LangChain processing error:', error);
      // Fallback to legacy method
      return await this.processQuestionLegacy(env, question);
    }
  }

  /**
   * Process question using legacy method
   */
  async processQuestionLegacy(env, question) {
    // Check cache first
    const cacheKey = `q:${question.toLowerCase().trim()}`;
    const cached = await this.getFromCache(env, cacheKey);
    
    if (cached) {
      return { answer: cached, cached: true };
    }

    // Get AI response
    const answer = await this.callAI(env, question);

    // Cache the response
    await this.putInCache(env, cacheKey, answer);

    return { answer, cached: false };
  }

  /**
   * Process a question (uses LangChain if enabled)
   */
  async processQuestion(env, question) {
    if (this.config.useLangchain) {
      return await this.processQuestionLangChain(env, question);
    } else {
      return await this.processQuestionLegacy(env, question);
    }
  }

  /**
   * Handle MCP tools/list request
   */
  handleMCPToolsList() {
    return {
      tools: [{
        name: this.config.mcpToolName || `${this.config.name.toLowerCase().replace(/\s+/g, '_')}_tool`,
        description: this.config.description,
        inputSchema: {
          type: 'object',
          properties: {
            question: {
              type: 'string',
              description: 'Question to ask the agent'
            }
          },
          required: ['question']
        }
      }]
    };
  }

  /**
   * Handle MCP tools/call request
   */
  async handleMCPToolCall(env, params) {
    const question = params?.arguments?.question;
    
    if (!question) {
      return {
        error: {
          code: -32602,
          message: 'Invalid params: question is required'
        }
      };
    }

    const result = await this.processQuestion(env, question);
    
    return {
      content: [{
        type: 'text',
        text: result.answer
      }]
    };
  }

  /**
   * Handle MCP requests
   */
  async handleMCPRequest(env, request) {
    const mcpRequest = await request.json();
    
    if (mcpRequest.method === 'tools/list') {
      return this.handleMCPToolsList();
    }
    
    if (mcpRequest.method === 'tools/call') {
      const toolName = this.config.mcpToolName || `${this.config.name.toLowerCase().replace(/\s+/g, '_')}_tool`;
      if (mcpRequest.params?.name === toolName) {
        return await this.handleMCPToolCall(env, mcpRequest.params);
      }
    }
    
    return {
      error: {
        code: -32601,
        message: 'Method not found'
      }
    };
  }

  /**
   * Get HTML page template
   */
  getHomePage() {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${this.config.name} - ${this.config.subtitle || 'AI Assistant'}</title>
    ${this.getStyles()}
</head>
<body>
    <header>
        <h1>${this.config.icon} ${this.config.name}</h1>
        <p class="subtitle">${this.config.subtitle || 'Powered by AI'}</p>
        ${this.config.useLangchain ? '<p class="tech-badge">🦜 LangChain.js Enhanced</p>' : ''}
    </header>
    
    <div class="container">
        <div class="chat-box">
            <div class="input-group">
                <input 
                    type="text" 
                    id="questionInput" 
                    placeholder="${this.config.placeholder || 'Ask a question...'}"
                    autofocus
                />
                <button id="askButton" onclick="askQuestion()">Ask</button>
            </div>
            
            <div id="messages" class="messages"></div>
            
            <div class="examples">
                <h3>Example Questions:</h3>
                <ul>
                    ${this.config.examples.map(ex => `<li>${ex}</li>`).join('\n                    ')}
                </ul>
            </div>
        </div>
    </div>
    
    <footer>
        <p>${this.config.footer || 'Built with Cloudflare Workers AI'}</p>
    </footer>
    
    ${this.getClientScript()}
</body>
</html>`;
  }

  /**
   * Get CSS styles (can be overridden)
   */
  getStyles() {
    return `<style>
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

        .tech-badge {
            text-align: center;
            color: #64ffda;
            font-size: 0.9rem;
            margin-top: 0.25rem;
            opacity: 0.8;
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
        
        .error {
            color: #ff6b6b;
            padding: 1rem;
            background: rgba(255, 107, 107, 0.1);
            border-radius: 5px;
            margin-top: 1rem;
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
    </style>`;
  }

  /**
   * Get client-side JavaScript (can be overridden)
   */
  getClientScript() {
    return `<script>
        const messagesDiv = document.getElementById('messages');
        const questionInput = document.getElementById('questionInput');
        const askButton = document.getElementById('askButton');
        
        questionInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                askQuestion();
            }
        });
        
        async function askQuestion() {
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
            
            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ question }),
                });
                
                const data = await response.json();
                
                // Remove loading message
                document.getElementById(loadingId)?.remove();
                
                if (response.ok) {
                    addMessage(data.answer, 'ai');
                } else {
                    addMessage('Error: ' + (data.error || 'Something went wrong'), 'ai');
                }
            } catch (error) {
                // Remove loading message
                document.getElementById(loadingId)?.remove();
                addMessage('Error: Could not connect to the server', 'ai');
            }
            
            // Re-enable input
            questionInput.disabled = false;
            askButton.disabled = false;
            questionInput.focus();
        }
        
        function addMessage(content, type, id) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + type + '-message';
            if (id) messageDiv.id = id;
            
            const label = document.createElement('div');
            label.className = 'message-label';
            label.textContent = type === 'user' ? 'You:' : '${this.config.aiLabel || 'AI Assistant'}:';
            
            const contentDiv = document.createElement('div');
            contentDiv.innerHTML = content;
            
            messageDiv.appendChild(label);
            messageDiv.appendChild(contentDiv);
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    </script>`;
  }

  /**
   * Main request handler
   */
  async fetch(request, env) {
    const url = new URL(request.url);
    const corsHeaders = this.getCorsHeaders();

    // Handle preflight requests
    if (request.method === 'OPTIONS') {
      return this.handleOptions();
    }

    // Serve homepage
    if (request.method === 'GET' && url.pathname === '/') {
      return new Response(this.getHomePage(), {
        headers: {
          'Content-Type': 'text/html',
          ...corsHeaders,
        },
      });
    }

    // Handle MCP requests
    if (request.method === 'POST' && url.pathname === '/mcp') {
      try {
        const result = await this.handleMCPRequest(env, request);
        return new Response(JSON.stringify(result), {
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders,
          },
        });
      } catch (error) {
        console.error('Error processing MCP request:', error);
        return new Response(JSON.stringify({
          error: {
            code: -32603,
            message: 'Internal error'
          }
        }), {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders,
          },
        });
      }
    }

    // Handle API requests
    if (request.method === 'POST' && url.pathname === '/api/ask') {
      try {
        const { question } = await request.json();
        
        if (!question || question.trim().length === 0) {
          return new Response(JSON.stringify({ error: 'Question is required' }), {
            status: 400,
            headers: {
              'Content-Type': 'application/json',
              ...corsHeaders,
            },
          });
        }

        const result = await this.processQuestion(env, question);

        return new Response(JSON.stringify(result), {
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders,
          },
        });

      } catch (error) {
        console.error('Error processing request:', error);
        return new Response(JSON.stringify({ 
          error: 'An error occurred processing your request' 
        }), {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders,
          },
        });
      }
    }

    // Handle SSE MCP endpoint for CopilotKit integration
    if (request.method === 'GET' && url.pathname === '/mcp/sse') {
      return this.handleSSERequest(request, env, url);
    }

    // Handle SSE message endpoint (POST for sending messages to SSE session)
    if (request.method === 'POST' && url.pathname === '/mcp/sse/message') {
      return this.handleSSEMessage(request, env, url);
    }

    // Return 404 for unhandled routes
    return new Response('Not Found', { status: 404 });
  }

  /**
   * Handle SSE (Server-Sent Events) MCP connection
   * This is required for CopilotKit MCP integration
   */
  async handleSSERequest(request, env, url) {
    const corsHeaders = this.getCorsHeaders();

    // Create SSE response headers
    const sseHeaders = {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      ...corsHeaders,
    };

    // Create a TransformStream for SSE
    const { readable, writable } = new TransformStream();
    const writer = writable.getWriter();
    const encoder = new TextEncoder();

    // Generate session ID for this SSE connection
    const sessionId = crypto.randomUUID();

    // Helper to send SSE events
    const sendEvent = async (event, data) => {
      const message = `event: ${event}\ndata: ${JSON.stringify(data)}\n\n`;
      await writer.write(encoder.encode(message));
    };

    // Start the SSE stream
    (async () => {
      try {
        // Send initial connection event with session info
        await sendEvent('open', {
          sessionId,
          protocol: 'mcp',
          version: '2024-11-05',
          capabilities: {
            tools: true,
            streaming: true
          }
        });

        // Send available tools
        const toolsList = this.handleMCPToolsList();
        await sendEvent('tools', toolsList);

        // Keep connection alive with periodic heartbeats
        const heartbeatInterval = setInterval(async () => {
          try {
            await sendEvent('heartbeat', { timestamp: Date.now() });
          } catch (e) {
            clearInterval(heartbeatInterval);
          }
        }, 30000); // 30 second heartbeat

        // Store session for message handling (in production, use KV or Durable Objects)
        // For now, we handle messages via the /mcp/sse/message endpoint

      } catch (error) {
        console.error('SSE stream error:', error);
        await sendEvent('error', { message: error.message });
      }
    })();

    return new Response(readable, {
      headers: sseHeaders,
    });
  }

  /**
   * Handle incoming SSE messages (tool calls)
   * CopilotKit sends tool calls via POST to this endpoint
   */
  async handleSSEMessage(request, env, url) {
    const corsHeaders = this.getCorsHeaders();

    try {
      const body = await request.json();
      const { method, params, id } = body;

      let result;

      if (method === 'tools/list') {
        result = this.handleMCPToolsList();
      } else if (method === 'tools/call') {
        result = await this.handleMCPToolCall(env, params);
      } else if (method === 'ping') {
        result = { pong: true, timestamp: Date.now() };
      } else {
        result = {
          error: {
            code: -32601,
            message: `Method not found: ${method}`
          }
        };
      }

      return new Response(JSON.stringify({
        jsonrpc: '2.0',
        id,
        result
      }), {
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders,
        },
      });

    } catch (error) {
      console.error('SSE message error:', error);
      return new Response(JSON.stringify({
        jsonrpc: '2.0',
        error: {
          code: -32603,
          message: 'Internal error'
        }
      }), {
        status: 500,
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders,
        },
      });
    }
  }

  /**
   * Stream a response via SSE for real-time AI responses
   * Can be used by the SSE connection for streaming chat responses
   */
  async *streamResponse(env, question) {
    // Check cache first
    const cacheKey = `q:${question.toLowerCase().trim()}`;
    const cached = await this.getFromCache(env, cacheKey);

    if (cached) {
      yield { type: 'cached', content: cached };
      return;
    }

    // For streaming, we'll yield chunks as they come
    // Note: Cloudflare Workers AI doesn't support true streaming yet,
    // so we simulate it by yielding the complete response
    const result = await this.processQuestion(env, question);

    // Simulate streaming by chunking the response
    const words = result.answer.split(' ');
    let chunk = '';

    for (let i = 0; i < words.length; i++) {
      chunk += (chunk ? ' ' : '') + words[i];

      // Yield every 5 words or at the end
      if ((i + 1) % 5 === 0 || i === words.length - 1) {
        yield { type: 'chunk', content: chunk };
        chunk = '';
      }
    }

    yield { type: 'done', cached: result.cached };
  }
}