// Auto-generated specialist agent

import { BaseAgent } from '../agent-framework/base-agent.js';

class {{cookiecutter.agent_class_name}}Agent extends BaseAgent {
  constructor() {
    super({
      name: '{{cookiecutter.project_name}}',
      description: '{{cookiecutter.description}}',
      icon: '{{cookiecutter.icon}}',
      subtitle: '{{cookiecutter.subtitle}}',
      systemPrompt: `{{cookiecutter.system_prompt}}

You are specialized in: {{cookiecutter.expertise}}

Focus your responses on your area of expertise and provide detailed, accurate information.`,
      placeholder: '{{cookiecutter.placeholder}}',
      examples: {{cookiecutter.examples_json}},
      aiLabel: '{{cookiecutter.ai_label}}',
      footer: '{{cookiecutter.footer}}',
      model: '{{cookiecutter.ai_model}}',
      maxTokens: {{cookiecutter.max_tokens}},
      temperature: {{cookiecutter.temperature}},
      cacheEnabled: {{cookiecutter.cache_enabled}},
      cacheTTL: {{cookiecutter.cache_ttl}},
      
      // Specialist configuration
      mcpToolName: '{{cookiecutter.mcp_tool_name}}',
      expertise: '{{cookiecutter.expertise}}',
      keywords: {{cookiecutter.keywords_json}},
      patterns: {{cookiecutter.patterns_json}},
      priority: {{cookiecutter.priority}}
    });
  }

  async processQuestion(env, question) {
    // Check if this question matches our expertise
    const isRelevant = this.isQuestionRelevant(question);
    
    if (!isRelevant) {
      return {
        answer: `This question appears to be outside my area of expertise ({{cookiecutter.expertise}}). I recommend consulting a more appropriate specialist.`,
        cached: false,
        relevant: false
      };
    }

    // Check cache first
    const cacheKey = `q:${question.toLowerCase().trim()}`;
    const cached = await this.getFromCache(env, cacheKey);
    
    if (cached) {
      return { answer: cached, cached: true, relevant: true };
    }

    // Generate specialized response
    const enhancedPrompt = `${this.config.systemPrompt}
    
As a specialist in {{cookiecutter.expertise}}, provide a detailed and authoritative response to the following question.`;

    const response = await env.AI.run(this.config.model, {
      messages: [
        { role: 'system', content: enhancedPrompt },
        { role: 'user', content: `Question: ${question}` }
      ],
      max_tokens: this.config.maxTokens,
      temperature: this.config.temperature,
    });

    const answer = response.response || 'I apologize, but I could not generate a response. Please try again.';

    // Cache the response
    await this.putInCache(env, cacheKey, answer);

    return { answer, cached: false, relevant: true };
  }

  isQuestionRelevant(question) {
    const lowerQuestion = question.toLowerCase();
    
    // Check keywords
    for (const keyword of this.config.keywords) {
      if (lowerQuestion.includes(keyword.toLowerCase())) {
        return true;
      }
    }
    
    // Check patterns
    for (const pattern of this.config.patterns) {
      try {
        const regex = new RegExp(pattern, 'i');
        if (regex.test(question)) {
          return true;
        }
      } catch (e) {
        console.error(`Invalid regex pattern: ${pattern}`, e);
      }
    }
    
    return false;
  }

  // MCP tool implementation
  async handleMCPRequest(request, env) {
    const body = await request.json();
    
    switch (body.method) {
      case 'tools/list':
        return new Response(JSON.stringify({
          tools: [{
            name: this.config.mcpToolName,
            description: this.config.description,
            inputSchema: {
              type: 'object',
              properties: {
                question: {
                  type: 'string',
                  description: 'The question to ask the specialist'
                }
              },
              required: ['question']
            }
          }]
        }), {
          headers: { 'Content-Type': 'application/json' }
        });
        
      case 'tools/call':
        if (body.params?.name === this.config.mcpToolName) {
          const result = await this.processQuestion(env, body.params.arguments.question);
          return new Response(JSON.stringify({
            content: [{
              type: 'text',
              text: result.answer
            }],
            metadata: {
              cached: result.cached,
              relevant: result.relevant,
              source: this.config.name,
              expertise: this.config.expertise
            }
          }), {
            headers: { 'Content-Type': 'application/json' }
          });
        }
        break;
    }
    
    return new Response(JSON.stringify({
      error: 'Method not found'
    }), {
      status: 404,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// Export default handler
export default {
  async fetch(request, env) {
    const agent = new {{cookiecutter.agent_class_name}}Agent();
    return agent.fetch(request, env);
  }
};