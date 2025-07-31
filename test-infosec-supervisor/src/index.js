// Auto-generated LangGraph agent
// Generated from configuration at 2025-07-31T05:25:35.717Z

import { LangGraphAgent } from '../agent-framework/langgraph-agent.js';

class InformationSecurityAIAssistantAgent extends LangGraphAgent {
  constructor() {
    super({
      name: 'Information Security AI Assistant',
      description: 'Advanced information security AI with specialized agent coordination using LangGraph Supervisor pattern',
      icon: '🛡️',
      subtitle: 'LangGraph Supervisor | Powered by MindHive.tech',
      systemPrompt: `You are an information security supervisor agent that coordinates four specialized security experts. Analyze incoming questions and intelligently route them to the most appropriate specialist based on the topic, complexity, and required expertise.

Your specialists include:
- Judge: Vulnerability assessment and compliance frameworks
- Lancer: Red teaming, penetration testing, and offensive security
- Scout: Network, endpoint, resource, and application discovery and fingerprinting
- Shield: Blue teaming, incident response, and active defense

Make intelligent routing decisions and coordinate responses for comprehensive security guidance.`,
      placeholder: 'Ask any information security question...',
      examples: ["What are the OWASP Top 10 vulnerabilities?","How do I perform reconnaissance on a target network?","What tools should I use for network discovery?","How do I respond to a ransomware attack?","What are the SOC 2 compliance requirements?"],
      aiLabel: 'InfoSec Supervisor',
      footer: 'Built with LangGraph and Cloudflare Workers AI | MindHive.tech',
      model: '@cf/meta/llama-3.1-8b-instruct',
      maxTokens: 1024,
      temperature: 0.4,
      cacheEnabled: true,
      cacheTTL: 3600,
      pattern: 'supervisor',
      maxIterations: 8,
      agents: {{JSON.stringify(agents)}},
      useLangchain: true
    });
  }
}

// Export default handler
export default {
  async fetch(request, env) {
    const agent = new InformationSecurityAIAssistantAgent();
    return agent.fetch(request, env);
  }
};