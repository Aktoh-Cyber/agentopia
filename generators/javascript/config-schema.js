/**
 * Configuration schemas for different agent types
 */

export const AGENT_TYPES = {
  ROUTER: 'router',
  SPECIALIST: 'specialist',
  SUPERVISOR: 'supervisor',
  NETWORK: 'network',
  HIERARCHICAL: 'hierarchical',
  COMMITTEE: 'committee',
  REFLECTION: 'reflection',
  PIPELINE: 'pipeline',
  AUTONOMOUS: 'autonomous'
};

/**
 * Base configuration schema
 */
export const BASE_CONFIG_SCHEMA = {
  // Agent Identity
  name: String,           // Required: "Cybersecurity AI Assistant"
  description: String,    // Required: "AI assistant for cybersecurity questions"
  icon: String,          // Optional: "🛡️"
  subtitle: String,      // Optional: "Powered by MindHive.tech"
  
  // AI Model Configuration
  model: String,         // Optional: "@cf/meta/llama-3.1-8b-instruct"
  systemPrompt: String,  // Required: System prompt for the AI
  maxTokens: Number,     // Optional: 512
  temperature: Number,   // Optional: 0.3
  
  // UI Configuration
  placeholder: String,   // Optional: "Ask a question..."
  examples: Array,       // Optional: ["What is...?", "How do I...?"]
  aiLabel: String,       // Optional: "AI Assistant"
  footer: String,        // Optional: "Built with..."
  
  // Features
  cacheEnabled: Boolean, // Optional: true
  cacheTTL: Number,      // Optional: 3600 (seconds)
  
  // MCP Configuration
  mcpToolName: String,   // Optional: Auto-generated from name
  
  // Deployment
  domain: String,        // Required: "cybersec.mindhive.tech"
  route: String,         // Optional: "cybersec.mindhive.tech/*"
  accountId: String,     // Required: Cloudflare account ID
  zoneId: String,        // Required: Cloudflare zone ID
};

/**
 * Router agent specific configuration
 */
export const ROUTER_CONFIG_SCHEMA = {
  ...BASE_CONFIG_SCHEMA,
  type: 'router',
  registry: {
    tools: Array,        // Array of tool configurations
    routingRules: Array, // Array of routing rules
  }
};

/**
 * Specialist agent specific configuration
 */
export const SPECIALIST_CONFIG_SCHEMA = {
  ...BASE_CONFIG_SCHEMA,
  type: 'specialist',
  expertise: String,     // Required: "vulnerability analysis"
  keywords: Array,       // Required: ["cve", "vulnerability"]
  patterns: Array,       // Optional: ["CVE-\\d{4}-\\d+"]
  priority: Number,      // Optional: 0-100
};

/**
 * Example configurations
 */
export const EXAMPLE_CONFIGS = {
  // Router agent (like cybersec-agent)
  cybersecRouter: {
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
    domain: 'cybersec.mindhive.tech',
    accountId: '82d842d586a0298981ab28617ec8ac66',
    zoneId: '4f8b8a0bd742d7872f75b8144b3851f8',
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
            'compliance', 'compliant', 'regulation', 'framework',
            'soc 2', 'soc2', 'iso 27001', 'iso27001', 'nist',
            'gdpr', 'hipaa', 'pci-dss', 'pci dss', 'pcidss'
          ],
          patterns: [
            'CVE-\\d{4}-\\d+',
            '\\b(SOC\\s*2|GDPR|HIPAA|PCI[- ]?DSS)\\b'
          ],
          priority: 10
        }
      ]
    }
  },

  // Specialist agent (like judge)
  judgeSpecialist: {
    type: 'specialist',
    name: 'Judge - Vulnerability & Compliance Expert',
    description: 'Specialized AI for vulnerability assessment and compliance frameworks',
    icon: '⚖️',
    subtitle: 'Specialized AI for Security Vulnerabilities and Compliance | MindHive.tech',
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
      'What is CVE-2021-44228 (Log4Shell) and how do I remediate it?',
      'What are the key requirements for SOC 2 Type II compliance?',
      'How do I calculate CVSS scores for vulnerabilities?',
      'What are the GDPR requirements for data breach notification?',
      'What controls are needed for PCI-DSS compliance at Level 1?'
    ],
    aiLabel: 'Judge',
    domain: 'judge.mindhive.tech',
    accountId: '82d842d586a0298981ab28617ec8ac66',
    zoneId: '4f8b8a0bd742d7872f75b8144b3851f8',
    expertise: 'vulnerability assessment and compliance',
    keywords: [
      'cve', 'vulnerability', 'vulnerabilities', 'exploit', 'patch',
      'cvss', 'score', 'severity', 'critical', 'high risk',
      'compliance', 'compliant', 'regulation', 'framework'
    ],
    patterns: [
      'CVE-\\d{4}-\\d+',
      '\\b(SOC\\s*2|GDPR|HIPAA|PCI[- ]?DSS)\\b'
    ],
    priority: 10
  },

  // Threat Intelligence specialist
  threatIntel: {
    type: 'specialist',
    name: 'Threat Intel - Advanced Threat Analysis',
    description: 'Specialized in threat intelligence, APT analysis, and attack attribution',
    icon: '🕵️',
    subtitle: 'Advanced Threat Intelligence and Analysis',
    systemPrompt: `You are a threat intelligence specialist focused on:
    - Advanced Persistent Threats (APTs) and attack campaigns
    - Threat actor profiling and attribution
    - Indicators of Compromise (IOCs) analysis
    - Tactics, Techniques, and Procedures (TTPs)
    - Threat landscape analysis and emerging threats
    - Malware analysis and reverse engineering insights
    
    Provide detailed threat intelligence with specific attribution, TTPs, and actionable threat hunting guidance.`,
    placeholder: 'Ask about threats, APTs, or threat intelligence...',
    examples: [
      'What are the TTPs of APT29?',
      'How do I hunt for Cobalt Strike beacons?',
      'What are the latest ransomware campaigns?',
      'How do I analyze this suspicious hash?',
      'What are indicators of compromise for this threat?'
    ],
    domain: 'threatintel.mindhive.tech',
    accountId: '82d842d586a0298981ab28617ec8ac66',
    zoneId: '4f8b8a0bd742d7872f75b8144b3851f8',
    expertise: 'threat intelligence and advanced threat analysis',
    keywords: [
      'apt', 'threat', 'malware', 'ioc', 'ttp',
      'campaign', 'attribution', 'actor', 'hunting',
      'ransomware', 'backdoor', 'c2', 'command control'
    ],
    patterns: [
      '\\b(APT\\d+|APT[A-Z]+)\\b',
      '\\b[a-fA-F0-9]{32,64}\\b', // Hash patterns
      '\\b(IOC|TTP|C2)\\b'
    ],
    priority: 8
  }
};

/**
 * Validation functions
 */
export function validateConfig(config) {
  const errors = [];
  
  if (!config.name) {
    errors.push('name is required');
  }
  
  if (!config.description) {
    errors.push('description is required');
  }
  
  if (!config.systemPrompt) {
    errors.push('systemPrompt is required');
  }
  
  if (!config.domain) {
    errors.push('domain is required');
  }
  
  if (!config.accountId) {
    errors.push('accountId is required');
  }
  
  if (!config.zoneId) {
    errors.push('zoneId is required');
  }
  
  if (config.type === 'router' && !config.registry) {
    errors.push('registry is required for router agents');
  }
  
  if (config.type === 'specialist' && !config.keywords) {
    errors.push('keywords are required for specialist agents');
  }
  
  // LangGraph pattern validations
  const langGraphPatterns = ['supervisor', 'network', 'hierarchical', 'committee', 'reflection', 'pipeline', 'autonomous'];
  if (langGraphPatterns.includes(config.type)) {
    if (!config.pattern) {
      errors.push('pattern is required for LangGraph agents');
    }
    if (!config.agents || !Array.isArray(config.agents)) {
      errors.push('agents array is required for LangGraph agents');
    }
  }
  
  return errors;
}

/**
 * Helper to get default config for agent type
 */
export function getDefaultConfig(type) {
  const baseDefaults = {
    model: '@cf/meta/llama-3.1-8b-instruct',
    maxTokens: 512,
    temperature: 0.3,
    cacheEnabled: true,
    cacheTTL: 3600,
    icon: '🤖',
    placeholder: 'Ask a question...',
    aiLabel: 'AI Assistant',
    footer: 'Built with Cloudflare Workers AI'
  };

  const langGraphPatterns = ['supervisor', 'network', 'hierarchical', 'committee', 'reflection', 'pipeline', 'autonomous'];

  switch (type) {
    case AGENT_TYPES.ROUTER:
      return {
        ...baseDefaults,
        type: 'router',
        registry: { tools: [] }
      };
    case AGENT_TYPES.SPECIALIST:
      return {
        ...baseDefaults,
        type: 'specialist',
        keywords: [],
        patterns: [],
        priority: 5
      };
    case AGENT_TYPES.SUPERVISOR:
    case AGENT_TYPES.NETWORK:
    case AGENT_TYPES.HIERARCHICAL:
    case AGENT_TYPES.COMMITTEE:
    case AGENT_TYPES.REFLECTION:
    case AGENT_TYPES.PIPELINE:
    case AGENT_TYPES.AUTONOMOUS:
      return {
        ...baseDefaults,
        type: type,
        pattern: type,
        maxIterations: 10,
        agents: [],
        useLangchain: true
      };
    default:
      throw new Error(`Unknown agent type: ${type}`);
  }
}