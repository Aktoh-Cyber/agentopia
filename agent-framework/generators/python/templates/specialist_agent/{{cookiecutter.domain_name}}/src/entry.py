# Auto-generated specialist agent
# Generated from configuration at {{cookiecutter.timestamp}}

from agent_framework import BaseAgent

# Configuration for {{cookiecutter.name}}
config = {
    'type': '{{cookiecutter.type}}',
    'name': '{{cookiecutter.name}}',
    'description': '{{cookiecutter.description}}',
    'icon': '{{cookiecutter.icon}}',
    'subtitle': '{{cookiecutter.subtitle}}',
    'systemPrompt': '''{{cookiecutter.systemPrompt}}''',
    'placeholder': '{{cookiecutter.placeholder}}',
    'examples': {{cookiecutter.examples_json}},
    'aiLabel': '{{cookiecutter.aiLabel}}',
    'footer': '{{cookiecutter.footer}}',
    'domain': '{{cookiecutter.domain}}',
    'model': '{{cookiecutter.model}}',
    'maxTokens': {{cookiecutter.maxTokens}},
    'temperature': {{cookiecutter.temperature}},
    'cacheEnabled': {{cookiecutter.cacheEnabled}},
    'cacheTTL': {{cookiecutter.cacheTTL}},
    'mcpToolName': '{{cookiecutter.mcpToolName}}',
    'expertise': '{{cookiecutter.expertise}}',
    'keywords': {{cookiecutter.keywords_json}},
    'patterns': {{cookiecutter.patterns_json}},
    'priority': {{cookiecutter.priority}}
}

# Create the specialist agent
{{cookiecutter.class_name|lower}} = BaseAgent(config)

# Export the fetch handler
async def on_fetch(request, env):
    """Main request handler for Cloudflare Workers"""
    return await {{cookiecutter.class_name|lower}}.fetch(request, env)