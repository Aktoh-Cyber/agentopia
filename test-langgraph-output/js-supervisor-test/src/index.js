// Auto-generated LangGraph agent
// Generated from configuration at 2025-07-31T04:02:28.089Z

import { LangGraphAgent } from '../agent-framework/langgraph-agent.js';

class supervisordemoAgent extends LangGraphAgent {
  constructor() {
    super({
      name: 'supervisor-demo',
      description: 'Supervisor pattern demonstration with multiple specialized agents',
      icon: '🤖',
      subtitle: '{{subtitle}}',
      systemPrompt: `You are a supervisor agent managing multiple specialized workers. Route tasks to the most appropriate specialist and coordinate their responses.`,
      placeholder: 'Ask a question...',
      examples: [],
      aiLabel: 'AI Assistant',
      footer: 'Built with Cloudflare Workers AI',
      model: '@cf/meta/llama-3.1-8b-instruct',
      maxTokens: 1024,
      temperature: 0.7,
      cacheEnabled: true,
      cacheTTL: 3600,
      pattern: 'supervisor',
      maxIterations: 10,
      agents: {{JSON.stringify(agents)}},
      useLangchain: true
    });
  }
}

// Export default handler
export default {
  async fetch(request, env) {
    const agent = new supervisordemoAgent();
    return agent.fetch(request, env);
  }
};