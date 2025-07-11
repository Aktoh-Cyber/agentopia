// Auto-generated specialist agent
// Generated from configuration at 2025-07-11T05:50:22.431Z

import { BaseAgent } from '../agent-framework/base-agent.js';

class ThreatIntelAdvancedThreatAnalysisAgent extends BaseAgent {
  constructor() {
    super({
      name: 'Threat Intel - Advanced Threat Analysis',
      description: 'Specialized in threat intelligence, APT analysis, and attack attribution',
      icon: '🕵️',
      subtitle: 'Advanced Threat Intelligence and Analysis | MindHive.tech',
      systemPrompt: `You are a threat intelligence specialist focused on:

- Advanced Persistent Threats (APTs) and attack campaigns
- Threat actor profiling and attribution
- Indicators of Compromise (IOCs) analysis
- Tactics, Techniques, and Procedures (TTPs)
- Threat landscape analysis and emerging threats
- Malware analysis and reverse engineering insights
- MITRE ATT&CK framework mapping

Provide detailed threat intelligence with specific attribution, TTPs, and actionable threat hunting guidance.
Include relevant IOCs, MITRE ATT&CK technique IDs, and detection strategies when applicable.`,
      placeholder: 'Ask about threats, APTs, or threat intelligence...',
      examples: ["What are the TTPs of APT29 (Cozy Bear)?","How do I hunt for Cobalt Strike beacons in my network?","What are the latest ransomware campaigns?","How do I analyze this suspicious hash: d41d8cd98f00b204e9800998ecf8427e?","What are indicators of compromise for the SolarWinds attack?"],
      aiLabel: 'Threat Intel',
      footer: 'Advanced Threat Intelligence | MindHive.tech',
      model: '@cf/meta/llama-3.1-8b-instruct',
      maxTokens: 512,
      temperature: 0.3,
      cacheEnabled: true,
      cacheTTL: 3600,
      mcpToolName: 'threat_intel_analysis'
    });
  }

  // Specialist agents use the base processQuestion implementation
  // The specialized system prompt handles the domain expertise
}

// Export default handler
export default {
  async fetch(request, env) {
    const agent = new ThreatIntelAdvancedThreatAnalysisAgent();
    return agent.fetch(request, env);
  }
};