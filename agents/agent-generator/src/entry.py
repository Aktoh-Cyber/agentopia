# Auto-generated specialist agent
# Generated from configuration at 2025-07-11T14:33:26.257921

from agent_framework.generator_agent import GeneratorAgent

# Configuration for Agent Generator
config = {
    'type': 'specialist',
    'name': 'Agent Generator',
    'description': 'Python-powered agent generator that creates and deploys new agents via GitHub integration',
    'icon': '🏭',
    'subtitle': 'Automated Agent Generation & GitOps Deployment | MindHive.tech',
    'systemPrompt': """You are a specialized agent generator that creates new AI agents based on user requirements. You can:

- Generate Python or JavaScript agents from configuration
- Create router agents that coordinate multiple specialists
- Create specialist agents for specific domains
- Commit generated agents to GitHub for automated deployment
- Manage agent dependencies and routing configurations

When a user requests a new agent, gather the required information:
- Agent type (router or specialist)
- Name and description
- Domain expertise or routing requirements
- Cloudflare domain and deployment details
- Language preference (Python or JavaScript)

Generate complete agent configurations and commit them to the repository for automated testing and deployment.""",
    'placeholder': 'Describe the agent you want to create...',
    'examples': ["Create a Python specialist agent for financial analysis", "Generate a JavaScript router that handles customer support queries", "Build a specialist agent for code security analysis", "Create a router agent that coordinates multiple AI specialists", "Generate an agent for threat intelligence and IOC analysis"],
    'aiLabel': 'Agent Generator',
    'footer': 'Automated Agent Generation | GitHub Integration | MindHive.tech',
    'domain': 'generator.mindhive.tech',
    'model': '@cf/meta/llama-3.1-8b-instruct',
    'maxTokens': 1024,
    'temperature': 0.2,
    'cacheEnabled': true,
    'cacheTTL': 1800,
    'mcpToolName': 'agent_generator',
    'expertise': 'agent generation and GitOps deployment',
    'keywords': ["generate", "create", "build", "agent", "specialist", "router", "python", "javascript", "deploy", "commit", "github", "configuration", "template", "framework", "worker", "cloudflare", "mcp", "routing", "automation"],
    'patterns': ["create\\s+(a|an)?\\s*(new\\s+)?(agent|specialist|router)", "generate\\s+(a|an)?\\s*(new\\s+)?(agent|specialist|router)", "build\\s+(a|an)?\\s*(new\\s+)?(agent|specialist|router)", "(python|javascript)\\s+(agent|specialist|router)", "deploy\\s+(agent|specialist|router)", "commit\\s+(agent|specialist|router)"],
    'priority': 15
}

# Create the agent generator agent
agentgeneratoragent = GeneratorAgent(config)

# Export the fetch handler
async def on_fetch(request, env):
    """Main request handler for Cloudflare Workers"""
    return await agentgeneratoragent.fetch(request, env)
