#!/usr/bin/env python3
"""
Python Agent Builder - Generates deployable Python agents from configuration
Uses cookiecutter for template generation
"""

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

try:
    from cookiecutter.main import cookiecutter
    from cookiecutter.exceptions import CookiecutterException
except ImportError:
    print("Please install cookiecutter: pip install cookiecutter")
    exit(1)


class PythonAgentBuilder:
    """Builder for Python Cloudflare Workers agents"""
    
    def __init__(self):
        self.script_dir = Path(__file__).parent
        self.templates_dir = self.script_dir / "templates"
    
    def validate_config(self, config: Dict[str, Any]) -> list:
        """Validate configuration"""
        errors = []
        
        required_fields = ['name', 'description', 'systemPrompt', 'domain', 'accountId', 'zoneId']
        for field in required_fields:
            if not config.get(field):
                errors.append(f'{field} is required')
        
        agent_type = config.get('type')
        if agent_type == 'router' and not config.get('registry'):
            errors.append('registry is required for router agents')
        
        if agent_type == 'specialist' and not config.get('keywords'):
            errors.append('keywords are required for specialist agents')
        
        return errors
    
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
            'footer': 'Built with Cloudflare Workers AI'
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
    
    def prepare_cookiecutter_context(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare context for cookiecutter template"""
        # Merge with defaults
        full_config = {**self.get_default_config(config['type']), **config}
        
        # Add computed fields
        full_config['timestamp'] = datetime.now().isoformat()
        full_config['domain_name'] = full_config['domain'].split('.')[0]
        full_config['base_domain'] = '.'.join(full_config['domain'].split('.')[1:])
        full_config['class_name'] = self.make_class_name(full_config['name'])
        full_config['examples_json'] = json.dumps(full_config.get('examples', []))
        full_config['registry_json'] = json.dumps(full_config.get('registry', {}), indent=2)
        full_config['keywords_json'] = json.dumps(full_config.get('keywords', []))
        full_config['patterns_json'] = json.dumps(full_config.get('patterns', []))
        
        return full_config
    
    def make_class_name(self, name: str) -> str:
        """Convert agent name to valid Python class name"""
        # Remove non-alphanumeric characters and convert to PascalCase
        words = ''.join(c if c.isalnum() or c.isspace() else ' ' for c in name).split()
        return ''.join(word.capitalize() for word in words) + 'Agent'
    
    def generate_agent(self, config: Dict[str, Any], output_dir: str) -> Dict[str, str]:
        """Generate a new agent from configuration"""
        # Validate configuration
        errors = self.validate_config(config)
        if errors:
            raise ValueError(f"Configuration validation failed: {', '.join(errors)}")
        
        # Prepare cookiecutter context
        context = self.prepare_cookiecutter_context(config)
        
        # Determine template directory based on agent type
        agent_type = config['type']
        template_dir = self.templates_dir / f"{agent_type}_agent"
        
        if not template_dir.exists():
            raise ValueError(f"Template not found for agent type: {agent_type}")
        
        # Generate using direct file templating (simpler than cookiecutter for our case)
        try:
            output_path = Path(output_dir) / context['domain_name']
            if output_path.exists():
                shutil.rmtree(output_path)
            
            # Create project directory structure
            output_path.mkdir(parents=True, exist_ok=True)
            (output_path / 'src').mkdir(exist_ok=True)
            (output_path / 'scripts').mkdir(exist_ok=True)
            
            # Generate files from templates
            template_files = {
                'src/entry.py': self.generate_entry_py(context),
                'wrangler.toml': self.generate_wrangler_toml(context),
                'scripts/deploy.sh': self.generate_deploy_script(context),
                'README.md': self.generate_readme(context),
                '.env.local.example': 'export CLOUDFLARE_API_TOKEN=your-token-here',
                '.gitignore': 'agent_framework/\n*.pyc\n__pycache__/\n.env\n.env.local\n*.log\n.wrangler/'
            }
            
            for file_path, content in template_files.items():
                full_path = output_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                
                # Make scripts executable
                if file_path.endswith('.sh'):
                    full_path.chmod(0o755)
            
            return {'project_dir': str(output_path)}
        
        except Exception as e:
            raise RuntimeError(f"Failed to generate agent: {e}")
    
    def generate_entry_py(self, context: Dict[str, Any]) -> str:
        """Generate entry.py file"""
        if context['type'] == 'router':
            import_line = "from agent_framework import RouterAgent"
            agent_class = "RouterAgent"
            config_extra = f"    'registry': {context['registry_json']}"
        else:
            import_line = "from agent_framework import BaseAgent"
            agent_class = "BaseAgent"
            config_extra = f"""    'mcpToolName': '{context['mcpToolName']}',
    'expertise': '{context['expertise']}',
    'keywords': {context['keywords_json']},
    'patterns': {context['patterns_json']},
    'priority': {context['priority']}"""
        
        return f'''# Auto-generated {context['type']} agent
# Generated from configuration at {context['timestamp']}

{import_line}

# Configuration for {context['name']}
config = {{
    'type': '{context['type']}',
    'name': '{context['name']}',
    'description': '{context['description']}',
    'icon': '{context['icon']}',
    'subtitle': '{context['subtitle']}',
    'systemPrompt': """{context['systemPrompt']}""",
    'placeholder': '{context['placeholder']}',
    'examples': {context['examples_json']},
    'aiLabel': '{context['aiLabel']}',
    'footer': '{context['footer']}',
    'domain': '{context['domain']}',
    'model': '{context['model']}',
    'maxTokens': {context['maxTokens']},
    'temperature': {context['temperature']},
    'cacheEnabled': {str(context['cacheEnabled']).lower()},
    'cacheTTL': {context['cacheTTL']},
{config_extra}
}}

# Create the {context['type']} agent
{context['class_name'].lower()} = {agent_class}(config)

# Export the fetch handler
async def on_fetch(request, env):
    """Main request handler for Cloudflare Workers"""
    return await {context['class_name'].lower()}.fetch(request, env)
'''
    
    def generate_wrangler_toml(self, context: Dict[str, Any]) -> str:
        """Generate wrangler.toml file"""
        return f'''name = "{context['domain_name']}"
main = "src/entry.py"
compatibility_date = "2024-01-01"
compatibility_flags = ["python_workers"]
account_id = "{context['accountId']}"

[ai]
binding = "AI"

[[kv_namespaces]]
binding = "CACHE"
id = "94f2859d6efd4fc8830887d5d797324a"

[vars]
MAX_TOKENS = "{context['maxTokens']}"
TEMPERATURE = "{context['temperature']}"

[[routes]]
pattern = "{context['domain']}/*"
zone_id = "{context['zoneId']}"
'''
    
    def generate_deploy_script(self, context: Dict[str, Any]) -> str:
        """Generate deployment script"""
        return f'''#!/bin/bash

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

echo -e "${{YELLOW}}{context['name']} Deployment${{NC}}"
echo "================================================"

# Check if CLOUDFLARE_API_TOKEN is set
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo -e "${{RED}}ERROR: CLOUDFLARE_API_TOKEN environment variable is required${{NC}}"
    exit 1
fi

ACCOUNT_ID="{context['accountId']}"
SCRIPT_NAME="{context['domain_name']}"
ZONE_ID="{context['zoneId']}"

echo -e "\\n${{YELLOW}}Deploying Python Worker to Cloudflare...${{NC}}"

if command -v wrangler &> /dev/null; then
    npx wrangler@latest deploy
    
    if [ $? -eq 0 ]; then
        echo -e "${{GREEN}}✓ Python Worker deployed successfully${{NC}}"
        echo ""
        echo "Your Python agent is now available at:"
        echo -e "${{YELLOW}}https://{context['domain']}${{NC}}"
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
    
    def generate_readme(self, context: Dict[str, Any]) -> str:
        """Generate README.md file"""
        examples_md = '\n'.join(f'- {ex}' for ex in context.get('examples', []))
        
        return f'''# {context['name']}

{context['description']}

🔗 **Live Demo**: https://{context['domain']}

## Features

- 🐍 Python-powered AI agent using Cloudflare Workers
- ⚡ Specialized expertise
- 💾 Response caching for improved performance
- 🎨 Clean, professional web interface
- 📡 RESTful API endpoint
- 🔌 MCP server interface for agent-to-agent communication
- 🚀 Fast cold starts with Pyodide optimization

## Configuration

This Python agent was generated from configuration with the following settings:

- **Type**: {context['type']}
- **Language**: Python 🐍
- **Model**: {context['model']}
- **Max Tokens**: {context['maxTokens']}
- **Temperature**: {context['temperature']}
- **Cache TTL**: {context['cacheTTL']} seconds

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

---

*Generated by Python Agent Framework v1.0 🐍*
'''
    
    def post_process_agent(self, project_dir: str, config: Dict[str, Any]):
        """Post-process generated agent"""
        project_path = Path(project_dir)
        
        # Make scripts executable
        scripts_dir = project_path / "scripts"
        if scripts_dir.exists():
            for script in scripts_dir.glob("*.sh"):
                script.chmod(0o755)
        
        # Copy agent framework if it doesn't exist
        framework_dir = project_path / "agent_framework"
        if not framework_dir.exists():
            source_framework = self.script_dir / "agent_framework"
            if source_framework.exists():
                shutil.copytree(source_framework, framework_dir)
        
        # Run black formatter if available
        try:
            subprocess.run(
                ["python", "-m", "black", str(project_path / "src")],
                check=False,
                capture_output=True
            )
        except (subprocess.SubprocessError, FileNotFoundError):
            pass  # Black not available, skip formatting


def build_agent_from_file(config_path: str, output_dir: str) -> Dict[str, str]:
    """CLI function to build an agent from configuration file"""
    # Read configuration
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    # Create builder and generate agent
    builder = PythonAgentBuilder()
    result = builder.generate_agent(config, output_dir)
    
    # Post-process
    builder.post_process_agent(result['project_dir'], config)
    
    print(f"✅ Python agent generated successfully at: {result['project_dir']}")
    return result


def main():
    """CLI entry point"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python agent_builder.py <config-file> <output-directory>")
        print("")
        print("Examples:")
        print("  python agent_builder.py configs/judge-specialist.json ../judge-py")
        print("  python agent_builder.py configs/cybersec-router.json ../cybersec-py")
        sys.exit(1)
    
    config_path = sys.argv[1]
    output_dir = sys.argv[2]
    
    try:
        build_agent_from_file(config_path, output_dir)
        
        print("")
        print("🚀 Next steps:")
        print(f"   1. cd {output_dir}")
        print("   2. Set your Cloudflare API token: export CLOUDFLARE_API_TOKEN='your-token'")
        print("   3. Deploy: ./scripts/deploy.sh")
        
    except Exception as e:
        print(f"❌ Error building agent: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()