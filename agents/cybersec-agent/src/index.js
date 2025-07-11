// New cybersec-agent using the agent framework
// This replaces the current index.js with a much cleaner implementation

import { RouterAgent } from '../agent-framework/router-agent.js';

// Configuration for cybersec-agent
const config = {
  type: 'router',
  name: 'Cybersecurity AI Assistant',
  description: 'AI assistant for cybersecurity questions with specialized agent routing',
  icon: '🛡️',
  subtitle: 'Powered by MindHive.tech',
  systemPrompt: `You are a cybersecurity expert assistant. Answer questions about information security, network security, cryptography, incident response, and security best practices.

Be concise but informative. If a question is not related to cybersecurity, politely redirect the conversation back to security topics.

Focus on practical, actionable advice that follows industry standards and best practices.`,
  placeholder: 'Ask a cybersecurity question...',
  examples: [
    'What are the OWASP Top 10 vulnerabilities?',
    'How can I secure my home network?',
    'What is the difference between encryption and hashing?',
    'How do I respond to a ransomware attack?',
    'What are best practices for password management?'
  ],
  aiLabel: 'CyberSec AI',
  footer: 'Built with Cloudflare Workers AI | MindHive.tech',
  domain: 'cybersec.mindhive.tech',
  model: '@cf/meta/llama-3.1-8b-instruct',
  maxTokens: 512,
  temperature: 0.3,
  cacheEnabled: true,
  cacheTTL: 3600,
  registry: {
    tools: [
      {
        id: 'judge',
        name: 'Judge - Vulnerability & Compliance Expert',
        description: 'Specialized in CVE analysis, compliance frameworks, and security assessments',
        endpoint: 'https://judge.mindhive.tech',
        mcpTool: 'judge_vulnerability_compliance',
        keywords: [
          'cve', 'vulnerability', 'vulnerabilities', 'exploit', 'patch',
          'cvss', 'score', 'severity', 'critical', 'high risk',
          'zero day', '0day', 'buffer overflow', 'sql injection',
          'xss', 'cross-site', 'csrf', 'remote code execution', 'rce',
          'compliance', 'compliant', 'regulation', 'framework',
          'soc 2', 'soc2', 'iso 27001', 'iso27001', 'nist',
          'gdpr', 'hipaa', 'pci-dss', 'pci dss', 'pcidss',
          'audit', 'control', 'requirement', 'certification',
          'sox', 'sarbanes', 'fedramp', 'ccpa', 'privacy'
        ],
        patterns: [
          'CVE-\\d{4}-\\d+',
          '\\b(SOC\\s*2|GDPR|HIPAA|PCI[- ]?DSS)\\b',
          'compliance.*(requirement|audit|framework)'
        ],
        priority: 10
      }
    ]
  }
};

// Create the router agent
const cybersecAgent = new RouterAgent(config);

// Export the worker
export default {
  async fetch(request, env) {
    return cybersecAgent.fetch(request, env);
  }
};