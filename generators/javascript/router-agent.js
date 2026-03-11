/**
 * Router Agent - Extends BaseAgent to route questions to specialized agents with LangChain.js
 */

import { BaseAgent } from './base-agent.js';
import { ToolRegistry, DynamicMCPClient } from './tool-registry.js';
import { ChatPromptTemplate } from "@langchain/core/prompts";
// Message types available but not directly used in this file
import { BaseChain } from "langchain/chains";

/**
 * Custom routing chain that analyzes questions and routes them appropriately
 */
class RouterChain extends BaseChain {
  constructor(llm, registry, mcpClient) {
    super();
    this.llm = llm;
    this.registry = registry;
    this.mcpClient = mcpClient;
    
    // Create routing analysis prompt
    this.routingPrompt = ChatPromptTemplate.fromTemplate(`
You are a routing assistant that analyzes questions and determines which specialized agent should handle them.

Available specialized agents:
{agentsSummary}

Analyze the question and respond with JSON in this format:
{{
  "shouldRoute": true/false,
  "agentName": "agent name if routing, null otherwise", 
  "confidence": 0-100,
  "reasoning": "brief explanation"
}}

Question: {question}
`);
  }

  async _call(inputs) {
    const { question } = inputs;
    
    // Get agents summary
    const agentsSummary = this.getAgentsSummary();
    
    try {
      // Run routing analysis
      const analysis = await this.llm._call(
        await this.routingPrompt.format({
          agentsSummary,
          question
        })
      );
      
      // Parse routing decision
      let routingDecision;
      try {
        // Extract JSON from response
        const jsonMatch = analysis.match(/\{[\s\S]*\}/);
        routingDecision = jsonMatch ? JSON.parse(jsonMatch[0]) : {
          shouldRoute: false,
          confidence: 0,
          reasoning: "Failed to parse routing decision"
        };
      } catch {
        routingDecision = {
          shouldRoute: false,
          confidence: 0,
          reasoning: "Failed to parse routing decision JSON"
        };
      }
      
      // If we should route and have high confidence, try the specialized agent
      if (routingDecision.shouldRoute && routingDecision.confidence > 70) {
        try {
          const toolResult = await this.mcpClient.askTool(question);
          if (toolResult) {
            return {
              routed: true,
              answer: toolResult.answer,
              source: toolResult.source,
              routingDecision
            };
          }
        } catch (error) {
          console.error('Failed to contact specialized agent:', error);
        }
      }
      
      // Otherwise, use tool registry scoring as fallback
      try {
        const toolResult = await this.mcpClient.askTool(question);
        if (toolResult) {
          return {
            routed: true,
            answer: toolResult.answer,
            source: toolResult.source,
            routingDecision
          };
        }
      } catch (error) {
        console.error('Tool registry routing failed:', error);
      }
      
      return {
        routed: false,
        routingDecision
      };
    } catch (error) {
      console.error('Routing chain error:', error);
      return {
        routed: false,
        routingDecision: {
          shouldRoute: false,
          confidence: 0,
          reasoning: `Routing error: ${error.message}`
        }
      };
    }
  }

  getAgentsSummary() {
    const tools = this.registry.getAllTools();
    if (tools.length === 0) {
      return "No specialized agents available.";
    }
    
    return tools.map(tool => 
      `- ${tool.name}: ${tool.description} (keywords: ${(tool.keywords || []).slice(0, 5).join(', ')})`
    ).join('\n');
  }

  _chainType() {
    return 'router_chain';
  }

  get inputKeys() {
    return ['question'];
  }

  get outputKeys() {
    return ['routed', 'answer', 'source', 'routingDecision'];
  }
}

export class RouterAgent extends BaseAgent {
  constructor(config) {
    super(config);
    
    // Initialize tool registry
    this.registry = new ToolRegistry(config.registry || { tools: [] });
    this.mcpClient = new DynamicMCPClient(this.registry);
    
    // Initialize router chain (will be set up when env is available)
    this.routerChain = null;
  }

  /**
   * Setup LangChain components with router chain.
   * Also initializes the Evolve Edge Bridge client if env vars are present.
   */
  setupLangChainComponents(env) {
    super.setupLangChainComponents(env);

    // Initialize Evolve Edge Bridge for cross-system tool routing
    if (env.EVOLVE_BRIDGE_URL && env.EVOLVE_SERVICE_TOKEN) {
      this.mcpClient.initEvolveBridge(env, {
        agentId: this.config.mcpToolName || this.config.name,
      });
    }

    if (this.config.useLangchain && this.llm) {
      this.routerChain = new RouterChain(this.llm, this.registry, this.mcpClient);
    }
  }

  /**
   * Process question using LangChain routing
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

    let answer;
    let source = this.config.name;

    // Try routing with LangChain
    if (this.routerChain) {
      try {
        const routingResult = await this.routerChain.call({ question });
        
        if (routingResult.routed) {
          answer = routingResult.answer;
          source = routingResult.source;
          
          // Add attribution
          answer = `${answer}\n\n*[This response was provided by ${source}]*`;
          
          // Log routing decision if available
          if (routingResult.routingDecision) {
            console.log('Routing decision:', JSON.stringify(routingResult.routingDecision));
          }
        }
      } catch (error) {
        console.error('LangChain routing failed:', error);
      }
    }

    // If no routing or it failed, use local AI with enhanced prompt
    if (!answer) {
      // Create enhanced prompt with routing awareness
      const enhancedPrompt = ChatPromptTemplate.fromTemplate(`
${this.config.systemPrompt}

Note: You have access to specialized agents for certain topics:
{toolSummary}
If a question is better suited for a specialized agent, mention it in your response.

Question: {question}
`);

      try {
        const result = await this.chain.call({
          question: question,
          toolSummary: this.getToolSummary()
        });

        answer = result.text || result.response || 'I apologize, but I could not generate a response.';
      } catch (error) {
        console.error('Enhanced prompt failed, using fallback:', error);
        // Fallback to legacy method
        return await this.processQuestionLegacy(env, question);
      }
    }

    // Cache the response
    await this.putInCache(env, cacheKey, answer);

    return { answer, cached: false, source };
  }

  /**
   * Process question using legacy routing
   */
  async processQuestionLegacy(env, question) {
    // Initialize Evolve bridge if not already done (legacy path)
    if (!this.mcpClient.evolveBridge && env.EVOLVE_BRIDGE_URL && env.EVOLVE_SERVICE_TOKEN) {
      this.mcpClient.initEvolveBridge(env, {
        agentId: this.config.mcpToolName || this.config.name,
      });
    }

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
   * Override processQuestion to implement routing logic
   */
  async processQuestion(env, question) {
    if (this.config.useLangchain) {
      return await this.processQuestionLangChain(env, question);
    } else {
      return await this.processQuestionLegacy(env, question);
    }
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
   * Override MCP tools list to include routing capabilities and Evolve bridge tools
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

    // Advertise Evolve bridge tools when the bridge is configured
    if (this.mcpClient.evolveBridge && this.mcpClient.evolveBridge.isConfigured()) {
      baseTool.tools.push({
        name: 'synapse_tool_invoke',
        description: 'Invoke a Synapse tool via the Evolve Edge Bridge (network scanning, vulnerability assessment, security hardening)',
        inputSchema: {
          type: 'object',
          properties: {
            tool: {
              type: 'string',
              description: 'Synapse tool name (e.g. synapse_nmap_scan, synapse_vuln_assess)'
            },
            arguments: {
              type: 'object',
              description: 'Arguments to pass to the Synapse tool'
            }
          },
          required: ['tool']
        }
      });
    }

    return baseTool;
  }

  /**
   * Handle additional MCP tool calls.
   * If the tool name matches an Evolve pattern, route it via the Edge Bridge.
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

    // Route Evolve-pattern tool calls through the bridge
    if (params?.name) {
      // Initialize bridge if needed
      if (!this.mcpClient.evolveBridge && env.EVOLVE_BRIDGE_URL && env.EVOLVE_SERVICE_TOKEN) {
        this.mcpClient.initEvolveBridge(env, {
          agentId: this.config.mcpToolName || this.config.name,
        });
      }

      const evolveResult = await this.mcpClient.askEvolveTool(params.name, params.arguments || {});
      if (evolveResult) {
        return {
          content: [{
            type: 'text',
            text: evolveResult.answer
          }]
        };
      }
    }

    return super.handleMCPToolCall(env, params);
  }

  /**
   * Override home page to show LangChain enhancement
   */
  getHomePage() {
    const basePage = super.getHomePage();
    
    // Add router-specific styling and info
    return basePage.replace(
      '<p class="subtitle">',
      `<p class="subtitle">Intelligent Agent Router</p>
       ${this.config.useLangchain ? '<p class="tech-badge">🦜 LangChain.js Enhanced Routing</p>' : ''}
       <p class="agent-count">${this.registry.getAllTools().length} Specialized Agents Available</p>
       <div style="text-align: center; margin-top: 0.5rem;">`
    ).replace(
      '</header>',
      '</div></header>'
    );
  }

  /**
   * Override styles to include router-specific styling
   */
  getStyles() {
    const baseStyles = super.getStyles();
    
    return baseStyles.replace(
      '.tech-badge {',
      `
        .agent-count {
            text-align: center;
            color: #ffd700;
            font-size: 0.9rem;
            margin-top: 0.25rem;
            opacity: 0.9;
        }
        
        .tech-badge {`
    );
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