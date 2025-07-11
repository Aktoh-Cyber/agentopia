/**
 * Router Agent - Extends BaseAgent to route questions to specialized agents
 */

import { BaseAgent } from './base-agent.js';
import { ToolRegistry, DynamicMCPClient } from './tool-registry.js';

export class RouterAgent extends BaseAgent {
  constructor(config) {
    super(config);
    
    // Initialize tool registry
    this.registry = new ToolRegistry(config.registry || { tools: [] });
    this.mcpClient = new DynamicMCPClient(this.registry);
  }

  /**
   * Override processQuestion to implement routing logic
   */
  async processQuestion(env, question) {
    // Check cache first
    const cacheKey = `q:${question.toLowerCase().trim()}`;
    const cached = await this.getFromCache(env, cacheKey);
    
    if (cached) {
      return { answer: cached, cached: true };
    }

    let answer;
    let source = this.config.name;

    // Try to route to specialized agent
    try {
      const toolResult = await this.mcpClient.askTool(question);
      
      if (toolResult) {
        answer = toolResult.answer;
        source = toolResult.source;
        
        // Add attribution
        answer = `${answer}\n\n*[This response was provided by ${source}]*`;
      }
    } catch (error) {
      console.error('Failed to contact specialized agent:', error);
      // Fall through to local AI
    }

    // If no specialized agent or it failed, use local AI
    if (!answer) {
      // Enhance system prompt with routing awareness
      const enhancedPrompt = `${this.config.systemPrompt}
      
Note: You have access to specialized agents for certain topics:
${this.getToolSummary()}
If a question is better suited for a specialized agent, mention it in your response.`;

      const response = await env.AI.run(this.config.model, {
        messages: [
          { role: 'system', content: enhancedPrompt },
          { role: 'user', content: `Question: ${question}` }
        ],
        max_tokens: this.config.maxTokens,
        temperature: this.config.temperature,
      });

      answer = response.response || 'I apologize, but I could not generate a response. Please try again.';
    }

    // Cache the response
    await this.putInCache(env, cacheKey, answer);

    return { answer, cached: false, source };
  }

  /**
   * Get a summary of available tools for the system prompt
   */
  getToolSummary() {
    const tools = this.registry.getAllTools();
    if (tools.length === 0) {
      return 'No specialized agents currently available.';
    }

    return tools.map(tool => 
      `- ${tool.name}: ${tool.description}`
    ).join('\n');
  }

  /**
   * Override MCP tools list to include routing capabilities
   */
  handleMCPToolsList() {
    const baseTool = super.handleMCPToolsList();
    
    // Add a tool for listing available agents
    baseTool.tools.push({
      name: 'list_available_agents',
      description: 'List all available specialized agents',
      inputSchema: {
        type: 'object',
        properties: {},
        required: []
      }
    });

    return baseTool;
  }

  /**
   * Handle additional MCP tool calls
   */
  async handleMCPToolCall(env, params) {
    if (params?.name === 'list_available_agents') {
      const tools = this.registry.getAllTools();
      return {
        content: [{
          type: 'text',
          text: JSON.stringify(tools, null, 2)
        }]
      };
    }

    return super.handleMCPToolCall(env, params);
  }

  /**
   * Add admin endpoint for managing tool registry
   */
  async fetch(request, env) {
    const url = new URL(request.url);
    const corsHeaders = this.getCorsHeaders();

    // Admin endpoint to update tool registry
    if (request.method === 'POST' && url.pathname === '/admin/tools') {
      try {
        // In production, add authentication here
        const { tool } = await request.json();
        this.registry.registerTool(tool);
        
        // Optionally persist to KV or D1
        if (env.REGISTRY) {
          await env.REGISTRY.put('tools', JSON.stringify(this.registry.toJSON()));
        }

        return new Response(JSON.stringify({ 
          success: true, 
          message: 'Tool registered successfully' 
        }), {
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders,
          },
        });
      } catch (error) {
        return new Response(JSON.stringify({ 
          success: false, 
          error: error.message 
        }), {
          status: 400,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders,
          },
        });
      }
    }

    // Admin endpoint to get current registry
    if (request.method === 'GET' && url.pathname === '/admin/tools') {
      return new Response(JSON.stringify(this.registry.toJSON()), {
        headers: {
          'Content-Type': 'application/json',
          ...corsHeaders,
        },
      });
    }

    // Delegate to base class for standard endpoints
    return super.fetch(request, env);
  }
}

/**
 * Factory function to create a router agent from config
 */
export function createRouterAgent(config) {
  return new RouterAgent(config);
}