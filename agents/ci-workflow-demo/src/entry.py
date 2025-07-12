# Auto-generated specialist agent
# Generated from configuration at 2025-07-11T17:33:36.713126

from agent_framework import BaseAgent

# Configuration for Judge - Vulnerability & Compliance Expert
config = {
    'type': 'specialist',
    'name': 'Judge - Vulnerability & Compliance Expert',
    'description': 'Specialized Python AI for vulnerability assessment and compliance frameworks',
    'icon': '⚖️',
    'subtitle': 'Specialized AI for Security Vulnerabilities and Compliance | MindHive.tech',
    'systemPrompt': """You are a specialized cybersecurity expert focused on vulnerability assessment and compliance. Your expertise includes:

- CVE database and vulnerability scoring (CVSS)
- Security frameworks (NIST, ISO 27001, SOC 2, GDPR, HIPAA, PCI-DSS)
- Vulnerability scanning and assessment methodologies
- Compliance auditing and gap analysis
- Risk assessment and remediation strategies
- Security controls and compensating measures

Provide detailed, authoritative answers about vulnerabilities, compliance requirements, and risk management.
Include specific CVE references, compliance clause numbers, and actionable remediation steps when relevant.
If a question is not related to vulnerabilities or compliance, politely redirect to these topics.""",
    'placeholder': 'Ask about vulnerabilities or compliance...',
    'examples': ["What is CVE-2021-44228 (Log4Shell) and how do I remediate it?", "What are the key requirements for SOC 2 Type II compliance?", "How do I calculate CVSS scores for vulnerabilities?", "What are the GDPR requirements for data breach notification?", "What controls are needed for PCI-DSS compliance at Level 1?"],
    'aiLabel': 'Judge',
    'footer': 'Specialized Security Intelligence | MindHive.tech | Python-Powered 🐍',
    'domain': 'judge-py.mindhive.tech',
    'model': '@cf/meta/llama-3.1-8b-instruct',
    'maxTokens': 512,
    'temperature': 0.3,
    'cacheEnabled': true,
    'cacheTTL': 3600,
    'mcpToolName': 'judge_vulnerability_compliance',
    'expertise': 'vulnerability assessment and compliance',
    'keywords': ["cve", "vulnerability", "vulnerabilities", "exploit", "patch", "cvss", "score", "severity", "critical", "high risk", "compliance", "compliant", "regulation", "framework", "soc 2", "soc2", "iso 27001", "iso27001", "nist", "gdpr", "hipaa", "pci-dss", "pci dss", "pcidss"],
    'patterns': ["CVE-\\d{4}-\\d+", "\\b(SOC\\s*2|GDPR|HIPAA|PCI[- ]?DSS)\\b"],
    'priority': 10
}

# Create the specialist agent
judgevulnerabilitycomplianceexpertagent = BaseAgent(config)

# Export the fetch handler
async def on_fetch(request, env):
    """Main request handler for Cloudflare Workers"""
    return await judgevulnerabilitycomplianceexpertagent.fetch(request, env)
