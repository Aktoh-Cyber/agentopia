# Auto-generated router agent
# Generated from configuration at {{cookiecutter.timestamp}}

from agent_framework import RouterAgent

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
    'registry': {{cookiecutter.registry_json}}
}

# Create the router agent
{{cookiecutter.class_name|lower}} = RouterAgent(config)

# Export the fetch handler
async def on_fetch(request, env):
    """Main request handler for Cloudflare Workers"""
    return await {{cookiecutter.class_name|lower}}.fetch(request, env)