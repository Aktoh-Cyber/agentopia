# Auto-generated router agent
# Generated from configuration at 2025-07-11T00:27:22.503646

from agent_framework import RouterAgent

# Configuration for Cybersecurity AI Assistant
config = {
    'type': 'router',
    'name': 'Cybersecurity AI Assistant',
    'description': 'Python-powered AI assistant for cybersecurity questions with specialized agent routing',
    'icon': '🛡️',
    'subtitle': 'Powered by MindHive.tech | Python Edition 🐍',
    'systemPrompt': """You are a cybersecurity expert assistant. Answer questions about information security, network security, cryptography, incident response, and security best practices.

Be concise but informative. If a question is not related to cybersecurity, politely redirect the conversation back to security topics.

Focus on practical, actionable advice that follows industry standards and best practices.""",
    'placeholder': 'Ask a cybersecurity question...',
    'examples': ["What are the OWASP Top 10 vulnerabilities?", "How can I secure my home network?", "What is the difference between encryption and hashing?", "How do I respond to a ransomware attack?", "What are best practices for password management?"],
    'aiLabel': 'CyberSec AI',
    'footer': 'Built with Cloudflare Workers AI & Python | MindHive.tech',
    'domain': 'cybersec-py.mindhive.tech',
    'model': '@cf/meta/llama-3.1-8b-instruct',
    'maxTokens': 512,
    'temperature': 0.3,
    'cacheEnabled': true,
    'cacheTTL': 3600,
    'registry': {
  "tools": [
    {
      "id": "judge-py",
      "name": "Judge - Vulnerability & Compliance Expert (Python)",
      "description": "Python-powered specialist in CVE analysis, compliance frameworks, and security assessments",
      "endpoint": "https://judge-py.mindhive.tech",
      "mcpTool": "judge_vulnerability_compliance",
      "keywords": [
        "cve",
        "vulnerability",
        "vulnerabilities",
        "exploit",
        "patch",
        "cvss",
        "score",
        "severity",
        "critical",
        "high risk",
        "zero day",
        "0day",
        "buffer overflow",
        "sql injection",
        "xss",
        "cross-site",
        "csrf",
        "remote code execution",
        "rce",
        "compliance",
        "compliant",
        "regulation",
        "framework",
        "soc 2",
        "soc2",
        "iso 27001",
        "iso27001",
        "nist",
        "gdpr",
        "hipaa",
        "pci-dss",
        "pci dss",
        "pcidss",
        "audit",
        "control",
        "requirement",
        "certification",
        "sox",
        "sarbanes",
        "fedramp",
        "ccpa",
        "privacy"
      ],
      "patterns": [
        "CVE-\\d{4}-\\d+",
        "\\b(SOC\\s*2|GDPR|HIPAA|PCI[- ]?DSS)\\b",
        "compliance.*(requirement|audit|framework)"
      ],
      "priority": 10
    }
  ]
}
}

# Create the router agent
cybersecurityaiassistantagent = RouterAgent(config)

# Export the fetch handler
async def on_fetch(request, env):
    """Main request handler for Cloudflare Workers"""
    return await cybersecurityaiassistantagent.fetch(request, env)
