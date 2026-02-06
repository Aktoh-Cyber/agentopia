// Auto-generated specialist agent
// Generated from configuration at 2026-02-05T19:30:19.635Z

import { BaseAgent } from '../agent-framework/base-agent.js';

class ScoutNetworkDiscoveryReconnaissanceExpertAgent extends BaseAgent {
  constructor() {
    super({
      name: 'Scout - Network Discovery & Reconnaissance Expert',
      description: 'Specialized AI for network mapping, reconnaissance, discovery, and information gathering',
      icon: '🔍',
      subtitle: 'Network Discovery & Reconnaissance Intelligence | MindHive.tech',
      systemPrompt: `You are a specialized reconnaissance and network discovery expert. Your expertise includes:

- Network mapping and topology discovery
- Port scanning and service enumeration (Nmap, Masscan)
- Service banner grabbing and version detection
- Web application discovery and crawling
- Open Source Intelligence (OSINT) gathering
- Asset discovery and inventory management
- DNS enumeration and subdomain discovery
- Technology fingerprinting and identification
- Passive reconnaissance techniques
- Whois and registrar information analysis

Provide detailed guidance on reconnaissance methodologies, discovery techniques, and information gathering.
Include specific tool recommendations, command syntax, and interpretation of results.
Always emphasize ethical and authorized reconnaissance practices only.
If a question is not related to reconnaissance or discovery, politely redirect to these topics.`,
      placeholder: 'Ask about network discovery or reconnaissance...',
      examples: ["What are the best tools for network mapping and discovery?","How do I enumerate services on a target system using Nmap?","What is the difference between active and passive reconnaissance?","How do I discover subdomains of a target domain?","What OSINT techniques can reveal information about an organization?"],
      aiLabel: 'Scout',
      footer: 'Specialized Network Intelligence | MindHive.tech',
      model: '@cf/meta/llama-3.1-8b-instruct',
      maxTokens: 512,
      temperature: 0.3,
      cacheEnabled: true,
      cacheTTL: 3600,
      mcpToolName: 'scout_discovery_reconnaissance'
    });
  }

  // Specialist agents use the base processQuestion implementation
  // The specialized system prompt handles the domain expertise
}

// Export default handler
export default {
  async fetch(request, env) {
    const agent = new ScoutNetworkDiscoveryReconnaissanceExpertAgent();
    return agent.fetch(request, env);
  }
};