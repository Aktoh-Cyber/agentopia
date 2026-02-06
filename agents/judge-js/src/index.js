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

  // Specialist agents use the base processQuestion implementation
  // The specialized system prompt handles the domain expertise
}

// Export default handler
export default {
  async fetch(request, env) {
    const agent = new JudgeVulnerabilityComplianceExpertAgent();
    return agent.fetch(request, env);
  }
};
