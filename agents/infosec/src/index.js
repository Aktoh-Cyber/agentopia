// InfoSec Supervisor Agent
// Routes security questions to specialized agents (Judge, Scout, Lancer, Shield)
// Generated for aktohcyber.com deployment

import { BaseAgent } from '../agent-framework/base-agent.js';

class InfoSecSupervisorAgent extends BaseAgent {
  constructor() {
    super({
      name: 'InfoSec Supervisor',
      description: 'Security operations supervisor that routes questions to specialist agents',
      icon: '🛡️',
      subtitle: 'Security Operations Intelligence | Horsemen Security',
      systemPrompt: `You are the InfoSec Supervisor, a senior security operations coordinator. Your role is to:

1. ANALYZE incoming security questions to determine the best specialist to handle them
2. ROUTE requests to the appropriate specialist agent:
   - Judge: Vulnerability assessment, CVE analysis, compliance frameworks (NIST, SOC2, GDPR, PCI-DSS)
   - Scout: Reconnaissance, OSINT, network discovery, threat intelligence gathering
   - Lancer: Penetration testing, red team operations, exploit development, offensive security
   - Shield: Incident response, threat hunting, blue team defense, security monitoring

3. COORDINATE complex security tasks that may require multiple specialists
4. SYNTHESIZE information from multiple sources into actionable intelligence

When responding:
- First identify the security domain the question relates to
- Recommend the appropriate specialist agent if the question is domain-specific
- For general security questions, provide a comprehensive response using your broad security expertise
- Always maintain a professional, security-focused perspective
- Include relevant frameworks, standards, or best practices when applicable

You have deep knowledge of:
- Security operations center (SOC) procedures
- Incident response frameworks (NIST, SANS)
- Threat intelligence analysis
- Security architecture and design
- Risk management and assessment
- Security awareness and training`,
      placeholder: 'Ask about security operations, get routed to the right specialist...',
      examples: [
        "What specialist should handle a CVE analysis request?",
        "How do I set up a security operations center?",
        "What's the difference between red team and penetration testing?",
        "Help me understand the MITRE ATT&CK framework",
        "What security controls are needed for a cloud deployment?"
      ],
      aiLabel: 'InfoSec',
      footer: 'Security Operations Supervisor | Horsemen Security Platform',
      model: '@cf/meta/llama-3.1-8b-instruct',
      maxTokens: 1024,
      temperature: 0.4,
      cacheEnabled: true,
      cacheTTL: 3600,
      mcpToolName: 'infosec_supervisor'
    });
  }

  // Override processQuestion to add routing logic
  async processQuestion(question, env) {
    // Analyze the question for routing keywords
    const routingKeywords = {
      judge: ['cve', 'vulnerability', 'compliance', 'nist', 'soc2', 'gdpr', 'pci', 'iso27001', 'cvss', 'audit'],
      scout: ['recon', 'osint', 'discovery', 'intelligence', 'footprint', 'enumerate', 'scan'],
      lancer: ['pentest', 'penetration', 'exploit', 'red team', 'attack', 'offensive', 'payload'],
      shield: ['incident', 'response', 'hunting', 'defense', 'blue team', 'detection', 'siem', 'monitor']
    };

    const lowerQuestion = question.toLowerCase();
    let suggestedAgent = null;
    let maxScore = 0;

    for (const [agent, keywords] of Object.entries(routingKeywords)) {
      const score = keywords.filter(kw => lowerQuestion.includes(kw)).length;
      if (score > maxScore) {
        maxScore = score;
        suggestedAgent = agent;
      }
    }

    // Add routing suggestion to the response
    const routingSuggestion = suggestedAgent
      ? `\n\n[Routing suggestion: This question may be best handled by the ${suggestedAgent.toUpperCase()} specialist agent at https://${suggestedAgent}.aktohcyber.com]`
      : '';

    // Use base class to process the question
    const response = await super.processQuestion(question, env);

    // Append routing suggestion if applicable
    if (typeof response === 'string' && routingSuggestion) {
      return response + routingSuggestion;
    }

    return response;
  }
}

// Export default handler
export default {
  async fetch(request, env) {
    // Rate limiting: 100 requests per minute per IP
    if (env.RATE_LIMITER) {
      const clientIP = request.headers.get('cf-connecting-ip') || 'unknown';
      const { success } = await env.RATE_LIMITER.limit({ key: clientIP });
      if (!success) {
        return new Response(JSON.stringify({ error: 'Rate limit exceeded. Please try again later.' }), {
          status: 429,
          headers: { 'Content-Type': 'application/json', 'Retry-After': '60' }
        });
      }
    }

    const agent = new InfoSecSupervisorAgent();
    return agent.fetch(request, env);
  }
};
