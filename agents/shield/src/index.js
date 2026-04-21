// Auto-generated specialist agent
// Generated from configuration at 2026-02-05T19:30:26.239Z

import { BaseAgent } from '../agent-framework/base-agent.js';

class ShieldBlueTeamIncidentResponseExpertAgent extends BaseAgent {
  constructor() {
    super({
      name: 'Shield - Blue Team & Incident Response Expert',
      description: 'Specialized AI for blue team operations, incident response, threat hunting, and defensive security',
      icon: '🛡️',
      subtitle: 'Defensive Security & Incident Response Intelligence | MindHive.tech',
      systemPrompt: `You are a specialized defensive security expert focused on blue team operations and incident response. Your expertise includes:

- Incident response procedures and playbooks
- Threat hunting methodologies and techniques
- SIEM rule development and tuning
- Digital forensics and evidence collection
- Malware analysis and reverse engineering
- Security monitoring and alerting strategies
- SOC operations and best practices
- Containment and eradication techniques
- Log analysis and event correlation
- Recovery and post-incident procedures

Provide detailed guidance on defensive operations, incident response procedures, and threat detection.
Include specific tool recommendations, methodology references, and practical implementation guidance.
Focus on detection, containment, eradication, and recovery strategies.
If a question is not related to defensive security or incident response, politely redirect to these topics.`,
      placeholder: 'Ask about incident response or threat hunting...',
      examples: ["What are the phases of incident response according to NIST?","How do I develop effective SIEM rules for threat detection?","What are indicators of compromise (IOCs) for ransomware attacks?","How do I perform threat hunting for suspicious command-line activity?","What steps should I take to contain a malware outbreak?"],
      aiLabel: 'Shield',
      footer: 'Specialized Defensive Security Intelligence | MindHive.tech',
      model: '@cf/meta/llama-3.1-8b-instruct',
      maxTokens: 512,
      temperature: 0.3,
      cacheEnabled: true,
      cacheTTL: 3600,
      mcpToolName: 'shield_blue_team_incident_response'
    });
  }

  // Specialist agents use the base processQuestion implementation
  // The specialized system prompt handles the domain expertise
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

    const agent = new ShieldBlueTeamIncidentResponseExpertAgent();
    return agent.fetch(request, env);
  }
};