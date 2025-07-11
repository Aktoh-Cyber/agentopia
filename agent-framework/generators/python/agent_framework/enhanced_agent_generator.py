"""
Enhanced Agent Generator with GitHub Integration
"""
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
from .github_client import GitHubMCPClient


class EnhancedAgentGenerator:
    """Enhanced agent generator that creates agents and commits them to GitHub"""
    
    def __init__(self, github_token: str, repo_owner: str, repo_name: str):
        self.github_client = GitHubMCPClient(github_token, repo_owner, repo_name)
        
    def get_default_config(self, agent_type: str) -> Dict[str, Any]:
        """Get default configuration for agent type"""
        defaults = {
            'model': '@cf/meta/llama-3.1-8b-instruct',
            'maxTokens': 512,
            'temperature': 0.3,
            'cacheEnabled': True,
            'cacheTTL': 3600,
            'icon': '🤖',
            'placeholder': 'Ask a question...',
            'aiLabel': 'AI Assistant',
            'footer': 'Built with Cloudflare Workers AI',
            'examples': []
        }
        
        if agent_type == 'router':
            defaults.update({
                'type': 'router',
                'registry': {'tools': []}
            })
        elif agent_type == 'specialist':
            defaults.update({
                'type': 'specialist',
                'keywords': [],
                'patterns': [],
                'priority': 5
            })
        
        return defaults
    
    def make_class_name(self, name: str) -> str:
        """Convert agent name to valid Python class name"""
        words = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in name).split()
        return ''.join(word.capitalize() for word in words) + 'Agent'
    
    def make_worker_name(self, name: str) -> str:
        """Convert agent name to valid worker name"""
        return ''.join(c if c.isalnum() or c in '-_' else '-' for c in name.lower()).strip('-')
    
    def make_domain_name(self, domain: str) -> str:
        """Extract domain name from full domain"""
        return domain.split('.')[0] if domain else 'agent'
    
    def generate_metadata(self, config: Dict[str, Any], language: str) -> str:
        """Generate .agent-metadata.json content"""
        metadata = {
            "generatedAt": datetime.now().isoformat(),
            "workerName": self.make_worker_name(config['name']),
            "domain": config['domain'],
            "type": config['type'],
            "language": language,
            "accountId": config['accountId'],
            "zoneId": config['zoneId'],
            "dependencies": []
        }
        
        # Add dependencies for router agents
        if config['type'] == 'router' and 'registry' in config:
            tools = config['registry'].get('tools', [])
            metadata["dependencies"] = [tool.get('id', '') for tool in tools if tool.get('id')]
        
        return json.dumps(metadata, indent=2)
    
    def generate_entry_py(self, config: Dict[str, Any]) -> str:
        """Generate entry.py file"""
        timestamp = datetime.now().isoformat()
        class_name = self.make_class_name(config['name'])
        
        if config['type'] == 'router':
            import_line = "from agent_framework import RouterAgent"
            agent_class = "RouterAgent"
            config_extra = f"    'registry': {json.dumps(config['registry'], indent=6)[6:]}"
        else:
            import_line = "from agent_framework import BaseAgent"
            agent_class = "BaseAgent"
            config_extra = f"""    'mcpToolName': '{config['mcpToolName']}',
    'expertise': '{config['expertise']}',
    'keywords': {json.dumps(config['keywords'])},
    'patterns': {json.dumps(config['patterns'])},
    'priority': {config['priority']}"""
        
        return f'''# Auto-generated {config['type']} agent
# Generated from configuration at {timestamp}

{import_line}

# Configuration for {config['name']}
config = {{
    'type': '{config['type']}',
    'name': '{config['name']}',
    'description': '{config['description']}',
    'icon': '{config['icon']}',
    'subtitle': '{config.get('subtitle', '')}',
    'systemPrompt': """{config['systemPrompt']}""",
    'placeholder': '{config['placeholder']}',
    'examples': {json.dumps(config['examples'])},
    'aiLabel': '{config['aiLabel']}',
    'footer': '{config['footer']}',
    'domain': '{config['domain']}',
    'model': '{config['model']}',
    'maxTokens': {config['maxTokens']},
    'temperature': {config['temperature']},
    'cacheEnabled': {str(config['cacheEnabled']).lower()},
    'cacheTTL': {config['cacheTTL']},
{config_extra}
}}

# Create the {config['type']} agent
{class_name.lower()} = {agent_class}(config)

# Export the fetch handler
async def on_fetch(request, env):
    """Main request handler for Cloudflare Workers"""
    return await {class_name.lower()}.fetch(request, env)
'''
    
    def generate_wrangler_toml(self, config: Dict[str, Any]) -> str:
        """Generate wrangler.toml file"""
        worker_name = self.make_worker_name(config['name'])
        
        return f'''name = "{worker_name}"
main = "src/entry.py"
compatibility_date = "2024-01-01"
compatibility_flags = ["python_workers"]
account_id = "{config['accountId']}"

[ai]
binding = "AI"

[[kv_namespaces]]
binding = "CACHE"
id = "94f2859d6efd4fc8830887d5d797324a"

[vars]
MAX_TOKENS = "{config['maxTokens']}"
TEMPERATURE = "{config['temperature']}"

[[routes]]
pattern = "{config['domain']}/*"
zone_id = "{config['zoneId']}"
'''
    
    def generate_deploy_script(self, config: Dict[str, Any]) -> str:
        """Generate deployment script"""
        worker_name = self.make_worker_name(config['name'])
        
        return f'''#!/bin/bash

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

echo -e "${{YELLOW}}{config['name']} Deployment${{NC}}"
echo "================================================"

# Check if CLOUDFLARE_API_TOKEN is set
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo -e "${{RED}}ERROR: CLOUDFLARE_API_TOKEN environment variable is required${{NC}}"
    exit 1
fi

ACCOUNT_ID="{config['accountId']}"
SCRIPT_NAME="{worker_name}"
ZONE_ID="{config['zoneId']}"

echo -e "\\n${{YELLOW}}Deploying Python Worker to Cloudflare...${{NC}}"

if command -v wrangler &> /dev/null; then
    npx wrangler@latest deploy
    
    if [ $? -eq 0 ]; then
        echo -e "${{GREEN}}✓ Python Worker deployed successfully${{NC}}"
        echo ""
        echo "Your Python agent is now available at:"
        echo -e "${{YELLOW}}https://{config['domain']}${{NC}}"
        echo ""
        echo "🐍 Python Workers Features:"
        echo "• Standard library support in production"
        echo "• Cloudflare AI and KV bindings"
        echo "• MCP server interface"
        echo "• Fast cold starts with Pyodide"
    else
        echo -e "${{RED}}✗ Failed to deploy Worker${{NC}}"
        exit 1
    fi
else
    echo -e "${{RED}}Wrangler not found. Please install: npm install -g wrangler${{NC}}"
    exit 1
fi
'''
    
    def generate_readme(self, config: Dict[str, Any]) -> str:
        """Generate README.md file"""
        examples_md = '\\n'.join(f'- {ex}' for ex in config.get('examples', []))
        
        return f'''# {config['name']}

{config['description']}

🔗 **Live Demo**: https://{config['domain']}

## Features

- 🐍 Python-powered AI agent using Cloudflare Workers
- ⚡ Specialized expertise in {config.get('expertise', 'various domains')}
- 💾 Response caching for improved performance
- 🎨 Clean, professional web interface
- 📡 RESTful API endpoint
- 🔌 MCP server interface for agent-to-agent communication
- 🚀 Fast cold starts with Pyodide optimization

## Configuration

This Python agent was auto-generated with the following settings:

- **Type**: {config['type'].title()}
- **Language**: Python 🐍
- **Model**: {config['model']}
- **Max Tokens**: {config['maxTokens']}
- **Temperature**: {config['temperature']}
- **Cache TTL**: {config['cacheTTL']} seconds

## Deployment

1. Set your Cloudflare API token:
   ```bash
   export CLOUDFLARE_API_TOKEN="your-token-here"
   ```

2. Deploy:
   ```bash
   ./scripts/deploy.sh
   ```

## Example Questions

{examples_md}

## MCP Integration

This agent is automatically available as an MCP server:
- **Endpoint**: `https://{config['domain']}/mcp`
- **Tool Name**: `{config.get('mcpToolName', config['name'].lower().replace(' ', '_'))}`

---

*Auto-generated by Agent Generator 🏭 at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
'''
    
    def generate_gitignore(self) -> str:
        """Generate .gitignore file for agent"""
        return '''agent_framework/
*.pyc
__pycache__/
.env
.env.local
*.log
.wrangler/
node_modules/
dist/
'''
    
    def generate_env_example(self) -> str:
        """Generate .env.local.example file"""
        return '''export CLOUDFLARE_API_TOKEN=your-token-here
'''
    
    def prepare_config(self, user_config: Dict[str, Any], language: str = "python") -> Dict[str, Any]:
        """Prepare and validate configuration"""
        # Merge with defaults
        config_type = user_config.get('type', 'specialist')
        full_config = {**self.get_default_config(config_type), **user_config}
        
        # Auto-generate missing fields
        if 'mcpToolName' not in full_config and config_type == 'specialist':
            full_config['mcpToolName'] = self.make_worker_name(full_config['name'])
        
        if 'expertise' not in full_config and config_type == 'specialist':
            full_config['expertise'] = full_config.get('description', 'specialized assistance')
        
        # Ensure required fields exist
        required_fields = ['name', 'description', 'systemPrompt', 'domain', 'accountId', 'zoneId']
        missing_fields = [field for field in required_fields if not full_config.get(field)]
        
        if missing_fields:
            raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
        
        return full_config
    
    def generate_agent_files(self, config: Dict[str, Any], language: str = "python") -> Dict[str, str]:
        """Generate all files for an agent"""
        prepared_config = self.prepare_config(config, language)
        
        files = {
            "src/entry.py": self.generate_entry_py(prepared_config),
            "wrangler.toml": self.generate_wrangler_toml(prepared_config),
            "scripts/deploy.sh": self.generate_deploy_script(prepared_config),
            "README.md": self.generate_readme(prepared_config),
            ".agent-metadata.json": self.generate_metadata(prepared_config, language),
            ".gitignore": self.generate_gitignore(),
            ".env.local.example": self.generate_env_example()
        }
        
        return files
    
    async def generate_and_commit_agent(self, user_config: Dict[str, Any], language: str = "python") -> Dict[str, Any]:
        """Complete workflow: generate agent and commit to GitHub"""
        try:
            # Generate all files
            generated_files = self.generate_agent_files(user_config, language)
            
            # Prepare final config
            final_config = self.prepare_config(user_config, language)
            
            # Commit to GitHub
            commit_result = await self.github_client.commit_agent(
                final_config, 
                generated_files, 
                language
            )
            
            return {
                "success": True,
                "agent_name": final_config['name'],
                "agent_type": final_config['type'],
                "language": language,
                "domain": final_config['domain'],
                "worker_name": self.make_worker_name(final_config['name']),
                "files_generated": list(generated_files.keys()),
                "github": commit_result,
                "next_steps": [
                    f"Review the pull request: {commit_result['pr_url']}",
                    "GitHub Actions will validate the configuration",
                    "Merge the PR to deploy the agent automatically",
                    f"Agent will be available at: https://{final_config['domain']}"
                ]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "agent_name": user_config.get('name', 'Unknown'),
                "suggestion": "Check your configuration and try again"
            }