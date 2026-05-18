// Judge - Vulnerability & Compliance Expert Agent
// Generated for aktohcyber.com deployment

import { BaseAgent } from '../agent-framework/base-agent.js';

class JudgeVulnerabilityComplianceExpertAgent extends BaseAgent {
  constructor() {
    super({
      name: 'Judge - Vulnerability & Compliance Expert',
      description: 'Specialized AI for vulnerability assessment and compliance frameworks',
      icon: '⚖️',
      subtitle: 'Vulnerability & Compliance Intelligence | Horsemen Security',
      systemPrompt: `You are a specialized cybersecurity expert focused on vulnerability assessment and compliance. Your expertise includes:

- CVE database and vulnerability scoring (CVSS)
- Security frameworks (NIST, ISO 27001, SOC 2, GDPR, HIPAA, PCI-DSS)
- Vulnerability scanning and assessment methodologies
- Compliance auditing and gap analysis
- Risk assessment and remediation strategies
- Security controls and compensating measures

Provide detailed, authoritative answers about vulnerabilities, compliance requirements, and risk management.
Include specific CVE references, compliance clause numbers, and actionable remediation steps when relevant.
If a question is not related to vulnerabilities or compliance, politely redirect to these topics.`,
      placeholder: 'Ask about vulnerabilities or compliance...',
      examples: [
        "What is CVE-2021-44228 (Log4Shell) and how do I remediate it?",
        "What are the key requirements for SOC 2 Type II compliance?",
        "How do I calculate CVSS scores for vulnerabilities?",
        "What are the GDPR requirements for data breach notification?",
        "What controls are needed for PCI-DSS compliance at Level 1?"
      ],
      aiLabel: 'Judge',
      footer: 'Specialized Security Intelligence | Horsemen Security Platform',
      model: '@cf/meta/llama-3.1-8b-instruct',
      maxTokens: 512,
      temperature: 0.3,
      cacheEnabled: true,
      cacheTTL: 3600,
      mcpToolName: 'judge_vulnerability_expert'
    });
  }

  /**
   * Gate 2: Attack Approval Endpoint (ADR-013)
   *
   * Evaluates whether a proposed attack should be approved based on:
   * - Target risk assessment
   * - Technique severity
   * - CVE context
   * - Compliance implications
   *
   * Called by Lancer agent before executing any attack operation.
   */
  async approveAttack(request, env) {
    const body = await request.json();
    const { target_id, technique_id, cve_id, agent } = body;

    if (!target_id || !technique_id) {
      return new Response(JSON.stringify({
        approved: false,
        reason: 'Missing required fields: target_id, technique_id',
        risk_level: 'unknown',
        conditions: [],
      }), { status: 400, headers: { 'Content-Type': 'application/json' } });
    }

    // Use AI to evaluate the attack request
    const prompt = `You are the Judge agent in a Four-Gate Approval System for attack simulation.
Evaluate the following attack request and respond with a JSON object.

Request:
- Target: ${target_id}
- Technique: ${technique_id} (MITRE ATT&CK)
- CVE: ${cve_id || 'N/A'}
- Requesting Agent: ${agent || 'unknown'}

Evaluate the risk and respond with ONLY a JSON object (no markdown):
{
  "approved": true/false,
  "reason": "brief explanation",
  "risk_level": "low|medium|high|critical",
  "conditions": ["any conditions for approval"]
}

Rules:
- Approve low/medium risk techniques against explicitly authorized targets
- Deny critical risk techniques unless conditions are met
- Always require sandbox execution for network-affecting techniques
- Never approve techniques that could cause data destruction`;

    try {
      const aiResponse = await env.AI.run(this.config.model, {
        messages: [{ role: 'user', content: prompt }],
        max_tokens: 256,
        temperature: 0.1,
      });

      let decision;
      try {
        const text = aiResponse.response || '';
        const jsonMatch = text.match(/\{[\s\S]*\}/);
        decision = jsonMatch ? JSON.parse(jsonMatch[0]) : {
          approved: false,
          reason: 'Failed to parse AI response',
          risk_level: 'high',
          conditions: [],
        };
      } catch {
        decision = {
          approved: false,
          reason: 'AI response parsing failed — defaulting to deny',
          risk_level: 'high',
          conditions: [],
        };
      }

      // Ensure required fields
      decision.approved = Boolean(decision.approved);
      decision.reason = decision.reason || 'No reason provided';
      decision.risk_level = decision.risk_level || 'unknown';
      decision.conditions = Array.isArray(decision.conditions) ? decision.conditions : [];

      return new Response(JSON.stringify(decision), {
        status: 200,
        headers: { 'Content-Type': 'application/json' },
      });
    } catch (err) {
      return new Response(JSON.stringify({
        approved: false,
        reason: `Judge evaluation error: ${err.message}`,
        risk_level: 'critical',
        conditions: [],
      }), { status: 500, headers: { 'Content-Type': 'application/json' } });
    }
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

    const agent = new JudgeVulnerabilityComplianceExpertAgent();

    // Gate 2: Attack approval endpoint (ADR-013)
    const url = new URL(request.url);
    if (request.method === 'POST' && url.pathname === '/api/approve_attack') {
      return agent.approveAttack(request, env);
    }

    return agent.fetch(request, env);
  }
};
