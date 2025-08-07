#!/usr/bin/env python
"""Post-generation hook for cookiecutter."""

import os
import json
import subprocess
from datetime import datetime

def process_templates():
    """Process template files and compute derived values."""
    
    # Get cookiecutter variables
    project_name = '{{cookiecutter.project_name}}'
    domain = '{{cookiecutter.domain}}'
    
    # Compute derived values
    subdomain = domain.split('.')[0] if '.' in domain else domain
    agent_class_name = ''.join(word.capitalize() for word in project_name.split())
    
    # Files to update
    files_to_update = [
        'src/index.js',
        'wrangler.toml',
        'README.md'
    ]
    
    # Replace placeholders - Using raw strings to avoid Jinja processing
    replacements = {
        '{' + '{cookiecutter.subdomain}' + '}': subdomain,
        '{' + '{cookiecutter.agent_class_name}' + '}': agent_class_name
    }
    
    for filepath in files_to_update:
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            
            for old, new in replacements.items():
                content = content.replace(old, new)
            
            with open(filepath, 'w') as f:
                f.write(content)
    
    print(f"✅ Processed templates with derived values:")
    print(f"   - Subdomain: {subdomain}")
    print(f"   - Agent Class: {agent_class_name}")

def validate_patterns():
    """Validate regex patterns in configuration."""
    try:
        patterns_json = '{{cookiecutter.patterns_json}}'
        patterns = json.loads(patterns_json)
        
        import re
        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.error as e:
                print(f"⚠️  Warning: Invalid regex pattern '{pattern}': {e}")
    except Exception as e:
        print(f"⚠️  Warning: Could not validate patterns: {e}")

def initialize_git():
    """Initialize git repository."""
    try:
        subprocess.run(['git', 'init'], check=True, capture_output=True)
        subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit from cookiecutter template'], 
                      check=True, capture_output=True)
        print("✅ Initialized git repository")
    except subprocess.CalledProcessError:
        print("⚠️  Could not initialize git repository (git may not be installed)")
    except Exception as e:
        print(f"⚠️  Git initialization failed: {e}")

def print_next_steps():
    """Print helpful next steps for the user."""
    project_slug = '{{cookiecutter.project_slug}}'
    domain = '{{cookiecutter.domain}}'
    mcp_tool_name = '{{cookiecutter.mcp_tool_name}}'
    
    print("\n" + "="*60)
    print(f"🎉 Successfully generated specialist agent: {project_slug}")
    print("="*60)
    print("\n📋 Next Steps:\n")
    print(f"1. cd {project_slug}")
    print("2. npm install")
    print("3. cp .env.local.example .env.local")
    print("4. Edit .env.local with your Cloudflare credentials")
    print("5. npx wrangler dev  # Run locally")
    print("\n🚀 Deploy to production:")
    print("   export CLOUDFLARE_API_TOKEN='your-token'")
    print("   ./scripts/deploy.sh")
    print(f"\n🔧 MCP Tool Name: {mcp_tool_name}")
    print(f"🌐 Domain: https://{domain}")
    print("\n📖 For integration with router agents, see README.md")
    print("="*60 + "\n")

def main():
    """Run post-generation tasks."""
    process_templates()
    validate_patterns()
    initialize_git()
    print_next_steps()

if __name__ == '__main__':
    main()