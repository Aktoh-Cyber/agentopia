/**
 * Base Agent Class
 * Foundation for all agents with Cloudflare Workers AI integration
 */

import { Ai } from '@cloudflare/ai';
import { CloudflareWorkersAIEmbeddings } from "@langchain/cloudflare";
import { CloudflareWorkersLLM } from "./cloudflare-llm.js";

export class BaseAgent {
  constructor(config = {}) {
    this.config = {
      name: 'Base Agent',
      description: 'A base AI agent',
      icon: '🤖',
      subtitle: 'Powered by Cloudflare Workers AI',
      systemPrompt: 'You are a helpful AI assistant.',
      placeholder: 'Ask me anything...',
      examples: [],
      aiLabel: 'AI',
      userLabel: 'You',
      footer: '',
      model: '@cf/meta/llama-3.1-70b-instruct',
      maxTokens: 1000,
      temperature: 0.7,
      cacheEnabled: true,
      cacheTTL: 3600,
      useLangchain: true,
      ...config
    };
    
    // Initialize LangChain LLM if enabled
    if (this.config.useLangchain) {
      this.llm = new CloudflareWorkersLLM({
        model: this.config.model,
        maxTokens: this.config.maxTokens,
        temperature: this.config.temperature
      });
    }
  }
  
  /**
   * Handle incoming requests
   */
  async handleRequest(request, env, ctx) {
    const url = new URL(request.url);
    
    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return this.handleCORS();
    }
    
    // Route based on path
    switch (url.pathname) {
      case '/':
        return request.method === 'GET'
          ? this.handleUIRequest(request, env)
          : this.handleChatRequest(request, env, ctx);
      
      case '/health':
        return this.handleHealthCheck(env);
      
      case '/mcp':
        return this.handleMCPRequest(request, env);
      
      case '/workflow/status':
        return this.handleWorkflowStatus(request, env);
      
      case '/workflow/cancel':
        return this.handleWorkflowCancel(request, env);
      
      case '/workflow/history':
        return this.handleWorkflowHistory(request, env);
      
      case '/workflow/retry':
        return this.handleWorkflowRetry(request, env);
      
      default:
        return new Response('Not Found', { status: 404 });
    }
  }
  
  /**
   * Handle chat requests
   */
  async handleChatRequest(request, env, ctx) {
    try {
      const { question } = await request.json();
      
      if (!question) {
        return this.jsonResponse({ error: 'Question is required' }, 400);
      }
      
      // Check cache if enabled
      if (this.config.cacheEnabled && env.KV) {
        const cached = await this.getCached(env.KV, question);
        if (cached) {
          return this.jsonResponse({ ...cached, cached: true });
        }
      }
      
      // Process the question
      const result = await this.processQuestion(env, question);
      
      // Cache the result if enabled
      if (this.config.cacheEnabled && env.KV) {
        ctx.waitUntil(this.cacheResult(env.KV, question, result));
      }
      
      return this.jsonResponse(result);
      
    } catch (error) {
      console.error('Chat request error:', error);
      return this.jsonResponse({ error: error.message }, 500);
    }
  }
  
  /**
   * Process a question (to be overridden by subclasses)
   */
  async processQuestion(env, question) {
    // Default implementation using Cloudflare AI
    const ai = new Ai(env.AI);
    
    const messages = [
      { role: 'system', content: this.config.systemPrompt },
      { role: 'user', content: question }
    ];
    
    const response = await ai.run(this.config.model, {
      messages,
      max_tokens: this.config.maxTokens,
      temperature: this.config.temperature
    });
    
    return {
      response: response.response,
      model: this.config.model,
      timestamp: new Date().toISOString()
    };
  }
  
  /**
   * Handle MCP protocol requests
   */
  async handleMCPRequest(request, env) {
    try {
      const { method, params } = await request.json();
      
      switch (method) {
        case 'tools/list':
          return this.jsonResponse({
            tools: [{
              name: this.config.name.toLowerCase().replace(/\s+/g, '_'),
              description: this.config.description,
              inputSchema: {
                type: 'object',
                properties: {
                  question: {
                    type: 'string',
                    description: 'The question or request to process'
                  }
                },
                required: ['question']
              }
            }]
          });
        
        case 'tools/call':
          const result = await this.processQuestion(env, params.arguments.question);
          return this.jsonResponse({ result });
        
        default:
          return this.jsonResponse({ error: 'Method not found' }, 404);
      }
    } catch (error) {
      return this.jsonResponse({ error: error.message }, 500);
    }
  }
  
  /**
   * Handle workflow status requests
   */
  async handleWorkflowStatus(request, env) {
    try {
      const url = new URL(request.url);
      const workflowId = url.searchParams.get('id');
      
      if (!workflowId) {
        return this.jsonResponse({ error: 'Workflow ID required' }, 400);
      }
      
      const status = await this.getWorkflowStatus(workflowId);
      return this.jsonResponse(status);
      
    } catch (error) {
      return this.jsonResponse({ error: error.message }, 500);
    }
  }
  
  /**
   * Handle workflow cancel requests
   */
  async handleWorkflowCancel(request, env) {
    try {
      const { workflowId } = await request.json();
      
      if (!workflowId) {
        return this.jsonResponse({ error: 'Workflow ID required' }, 400);
      }
      
      // Implementation would cancel the workflow
      return this.jsonResponse({ 
        success: true, 
        message: `Workflow ${workflowId} cancelled` 
      });
      
    } catch (error) {
      return this.jsonResponse({ error: error.message }, 500);
    }
  }
  
  /**
   * Handle workflow history requests
   */
  async handleWorkflowHistory(request, env) {
    try {
      const url = new URL(request.url);
      const limit = parseInt(url.searchParams.get('limit') || '10');
      const status = url.searchParams.get('status');
      
      // Implementation would fetch workflow history
      const history = [];
      
      return this.jsonResponse({ history, limit, status });
      
    } catch (error) {
      return this.jsonResponse({ error: error.message }, 500);
    }
  }
  
  /**
   * Handle workflow retry requests
   */
  async handleWorkflowRetry(request, env) {
    try {
      const { workflowId } = await request.json();
      
      if (!workflowId) {
        return this.jsonResponse({ error: 'Workflow ID required' }, 400);
      }
      
      // Implementation would retry the workflow
      return this.jsonResponse({ 
        success: true, 
        message: `Retrying workflow ${workflowId}`,
        newWorkflowId: crypto.randomUUID()
      });
      
    } catch (error) {
      return this.jsonResponse({ error: error.message }, 500);
    }
  }
  
  /**
   * Handle UI requests
   */
  async handleUIRequest(request, env) {
    const html = this.generateHTML();
    return new Response(html, {
      headers: {
        'Content-Type': 'text/html',
        'Cache-Control': 'public, max-age=3600'
      }
    });
  }
  
  /**
   * Handle health check
   */
  async handleHealthCheck(env) {
    return this.jsonResponse({
      status: 'healthy',
      agent: this.config.name,
      timestamp: new Date().toISOString()
    });
  }
  
  /**
   * Handle CORS
   */
  handleCORS() {
    return new Response(null, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '86400'
      }
    });
  }
  
  /**
   * Get cached result
   */
  async getCached(kv, question) {
    try {
      const key = `cache:${this.hashQuestion(question)}`;
      const cached = await kv.get(key, 'json');
      return cached;
    } catch (error) {
      console.error('Cache get error:', error);
      return null;
    }
  }
  
  /**
   * Cache result
   */
  async cacheResult(kv, question, result) {
    try {
      const key = `cache:${this.hashQuestion(question)}`;
      await kv.put(key, JSON.stringify(result), {
        expirationTtl: this.config.cacheTTL
      });
    } catch (error) {
      console.error('Cache put error:', error);
    }
  }
  
  /**
   * Hash question for cache key
   */
  hashQuestion(question) {
    // Simple hash for demo - in production use crypto
    return btoa(question).replace(/[^a-zA-Z0-9]/g, '').substring(0, 32);
  }
  
  /**
   * JSON response helper
   */
  jsonResponse(data, status = 200) {
    return new Response(JSON.stringify(data), {
      status,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*'
      }
    });
  }
  
  /**
   * Generate HTML UI
   */
  generateHTML() {
    return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${this.config.name}</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px; }
        .container { background: white; border-radius: 20px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); max-width: 800px; width: 100%; overflow: hidden; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; }
        .header h1 { font-size: 2em; margin-bottom: 10px; display: flex; align-items: center; justify-content: center; gap: 10px; }
        .header .subtitle { opacity: 0.9; font-size: 1.1em; }
        .workflow-status { background: rgba(255,255,255,0.1); border-radius: 10px; padding: 15px; margin-top: 20px; }
        .workflow-status h3 { margin-bottom: 10px; }
        .status-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 10px; margin-top: 10px; }
        .status-item { background: rgba(255,255,255,0.2); padding: 8px; border-radius: 5px; text-align: center; }
        .chat-container { height: 500px; display: flex; flex-direction: column; }
        .messages { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 15px; }
        .message { padding: 15px; border-radius: 15px; max-width: 70%; word-wrap: break-word; }
        .message.user { background: #f0f2f5; align-self: flex-end; margin-left: auto; }
        .message.ai { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; align-self: flex-start; }
        .message .label { font-size: 0.85em; opacity: 0.7; margin-bottom: 5px; }
        .input-container { padding: 20px; border-top: 1px solid #e0e0e0; display: flex; gap: 10px; }
        .input-container input { flex: 1; padding: 12px 20px; border: 2px solid #e0e0e0; border-radius: 25px; font-size: 16px; outline: none; transition: border-color 0.3s; }
        .input-container input:focus { border-color: #667eea; }
        .input-container button { padding: 12px 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; border: none; border-radius: 25px; font-size: 16px; cursor: pointer; transition: transform 0.2s; }
        .input-container button:hover { transform: scale(1.05); }
        .input-container button:disabled { opacity: 0.5; cursor: not-allowed; }
        .examples { padding: 15px 20px; background: #f8f9fa; display: flex; gap: 10px; flex-wrap: wrap; }
        .example-chip { padding: 8px 15px; background: white; border: 1px solid #e0e0e0; border-radius: 20px; font-size: 14px; cursor: pointer; transition: all 0.3s; }
        .example-chip:hover { background: #667eea; color: white; transform: scale(1.05); }
        .loading { display: none; padding: 15px; text-align: center; }
        .loading.active { display: block; }
        .loading-spinner { display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #667eea; border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .footer { padding: 15px; text-align: center; color: #666; font-size: 0.9em; background: #f8f9fa; }
        .workflow-step { display: inline-block; padding: 5px 10px; margin: 2px; background: rgba(255,255,255,0.3); border-radius: 5px; font-size: 0.9em; }
        .workflow-step.completed { background: rgba(76, 175, 80, 0.3); }
        .workflow-step.in-progress { background: rgba(255, 193, 7, 0.3); animation: pulse 2s infinite; }
        .workflow-step.failed { background: rgba(244, 67, 54, 0.3); }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1><span>${this.config.icon}</span> ${this.config.name}</h1>
            <div class="subtitle">${this.config.subtitle}</div>
            <div class="workflow-status">
                <h3>Workflow Orchestration</h3>
                <div class="status-grid">
                    <div class="status-item">
                        <div>Strategy</div>
                        <strong>${this.config.supervisorStrategy || 'Sequential'}</strong>
                    </div>
                    <div class="status-item">
                        <div>Agents</div>
                        <strong>${this.specialistAgents ? this.specialistAgents.length : 0}</strong>
                    </div>
                    <div class="status-item">
                        <div>Steps</div>
                        <strong>${this.workflowSteps ? this.workflowSteps.length : 0}</strong>
                    </div>
                </div>
                <div id="workflowSteps" style="margin-top: 10px;"></div>
            </div>
        </div>
        
        ${this.config.examples && this.config.examples.length > 0 ? `
        <div class="examples">
            ${this.config.examples.map(ex => `<div class="example-chip" onclick="sendExample('${ex}')">${ex}</div>`).join('')}
        </div>
        ` : ''}
        
        <div class="chat-container">
            <div class="messages" id="messages"></div>
            <div class="loading" id="loading">
                <div class="loading-spinner"></div>
                <div style="margin-top: 10px;">Orchestrating workflow...</div>
            </div>
        </div>
        
        <div class="input-container">
            <input type="text" id="input" placeholder="${this.config.placeholder}" onkeypress="if(event.key==='Enter')sendMessage()">
            <button onclick="sendMessage()" id="sendBtn">Send</button>
        </div>
        
        ${this.config.footer ? `<div class="footer">${this.config.footer}</div>` : ''}
    </div>
    
    <script>
        let workflowInterval = null;
        
        function sendMessage() {
            const input = document.getElementById('input');
            const question = input.value.trim();
            if (!question) return;
            
            addMessage(question, 'user');
            input.value = '';
            
            document.getElementById('loading').classList.add('active');
            document.getElementById('sendBtn').disabled = true;
            
            fetch('/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question })
            })
            .then(res => res.json())
            .then(data => {
                document.getElementById('loading').classList.remove('active');
                document.getElementById('sendBtn').disabled = false;
                
                if (data.error) {
                    addMessage('Error: ' + data.error, 'ai');
                } else {
                    addMessage(data.response, 'ai');
                    if (data.workflowId) {
                        updateWorkflowStatus(data);
                    }
                }
            })
            .catch(err => {
                document.getElementById('loading').classList.remove('active');
                document.getElementById('sendBtn').disabled = false;
                addMessage('Error: ' + err.message, 'ai');
            });
        }
        
        function sendExample(text) {
            document.getElementById('input').value = text;
            sendMessage();
        }
        
        function addMessage(text, type) {
            const messages = document.getElementById('messages');
            const message = document.createElement('div');
            message.className = 'message ' + type;
            
            const label = document.createElement('div');
            label.className = 'label';
            label.textContent = type === 'user' ? '${this.config.userLabel || 'You'}' : '${this.config.aiLabel || 'AI'}';
            
            const content = document.createElement('div');
            content.textContent = text;
            
            message.appendChild(label);
            message.appendChild(content);
            messages.appendChild(message);
            messages.scrollTop = messages.scrollHeight;
        }
        
        function updateWorkflowStatus(data) {
            const stepsDiv = document.getElementById('workflowSteps');
            stepsDiv.innerHTML = '';
            
            if (data.completedSteps) {
                data.completedSteps.forEach(step => {
                    const stepEl = document.createElement('span');
                    stepEl.className = 'workflow-step completed';
                    stepEl.textContent = '✓ ' + step;
                    stepsDiv.appendChild(stepEl);
                });
            }
            
            if (data.metadata && data.metadata.errors) {
                data.metadata.errors.forEach(err => {
                    const stepEl = document.createElement('span');
                    stepEl.className = 'workflow-step failed';
                    stepEl.textContent = '✗ ' + err.step;
                    stepsDiv.appendChild(stepEl);
                });
            }
        }
    </script>
</body>
</html>`;
  }
}