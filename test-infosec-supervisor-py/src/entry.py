# Auto-generated supervisor agent
# Generated from configuration at 2025-07-30T23:26:50.138189

from agent_framework.langgraph_agent import LangGraphAgent

# Configuration for Information Security AI Assistant
config = {
    'type': 'supervisor',
    'name': 'Information Security AI Assistant',
    'description': 'Advanced information security AI with specialized agent coordination using LangGraph Supervisor pattern',
    'icon': '🛡️',
    'subtitle': 'LangGraph Supervisor | Powered by MindHive.tech',
    'systemPrompt': """You are an information security supervisor agent that coordinates four specialized security experts. Analyze incoming questions and intelligently route them to the most appropriate specialist based on the topic, complexity, and required expertise.

Your specialists include:
- Judge: Vulnerability assessment and compliance frameworks
- Lancer: Red teaming, penetration testing, and offensive security
- Scout: Network, endpoint, resource, and application discovery and fingerprinting
- Shield: Blue teaming, incident response, and active defense

Make intelligent routing decisions and coordinate responses for comprehensive security guidance.""",
    'placeholder': 'Ask any information security question...',
    'examples': ["What are the OWASP Top 10 vulnerabilities?", "How do I perform reconnaissance on a target network?", "What tools should I use for network discovery?", "How do I respond to a ransomware attack?", "What are the SOC 2 compliance requirements?"],
    'aiLabel': 'InfoSec Supervisor',
    'footer': 'Built with LangGraph and Cloudflare Workers AI | MindHive.tech',
    'domain': 'infosec.mindhive.tech',
    'model': '@cf/meta/llama-3.1-8b-instruct',
    'maxTokens': 1024,
    'temperature': 0.4,
    'cacheEnabled': true,
    'cacheTTL': 3600,
    'pattern': 'supervisor',
    'maxIterations': 8,
    'agents': [
  {
    "name": "judge",
    "expertise": "Vulnerability assessment, CVE analysis, compliance frameworks (SOC 2, GDPR, HIPAA, PCI-DSS, ISO 27001, NIST), security auditing, and regulatory requirements",
    "description": "Expert in vulnerability scoring, compliance requirements, and security assessment methodologies",
    "specializes_in": [
      "CVE analysis and CVSS scoring",
      "Compliance frameworks and auditing",
      "Vulnerability scanning and assessment",
      "Security controls and requirements",
      "Risk assessment and gap analysis"
    ]
  },
  {
    "name": "lancer",
    "expertise": "Red teaming, penetration testing, exploit development, social engineering, privilege escalation, and offensive security techniques",
    "description": "Specialist in offensive security, ethical hacking, and penetration testing methodologies",
    "specializes_in": [
      "Penetration testing methodologies (OWASP, NIST, PTES)",
      "Exploit development and payload creation",
      "Social engineering and phishing campaigns",
      "Privilege escalation techniques",
      "Red team operations and adversary simulation"
    ]
  },
  {
    "name": "scout",
    "expertise": "Network discovery, port scanning, service enumeration, application fingerprinting, OSINT gathering, and reconnaissance techniques",
    "description": "Expert in reconnaissance, discovery, and information gathering across networks and applications",
    "specializes_in": [
      "Network mapping and port scanning (Nmap, Masscan)",
      "Service enumeration and banner grabbing",
      "Web application discovery and crawling",
      "OSINT techniques and passive reconnaissance",
      "Asset discovery and inventory management"
    ]
  },
  {
    "name": "shield",
    "expertise": "Blue teaming, incident response, threat hunting, SOC operations, SIEM management, and defensive security measures",
    "description": "Specialist in defensive security, incident response, and proactive threat detection",
    "specializes_in": [
      "Incident response procedures and playbooks",
      "Threat hunting methodologies and techniques",
      "SIEM rule development and tuning",
      "Digital forensics and malware analysis",
      "SOC operations and monitoring strategies"
    ]
  }
],
    'useLangchain': true
}

# Create the supervisor agent
informationsecurityaiassistantagent = LangGraphAgent(config)

# Export the fetch handler
async def on_fetch(request, env):
    """Main request handler for Cloudflare Workers"""
    return await informationsecurityaiassistantagent.fetch(request, env)
