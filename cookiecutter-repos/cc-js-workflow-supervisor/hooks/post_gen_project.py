#!/usr/bin/env python
"""Post-generation hook for JavaScript workflow supervisor template."""

import os
import subprocess
import json


def make_scripts_executable():
    """Make deployment scripts executable."""
    scripts = ['scripts/deploy.sh']
    for script in scripts:
        if os.path.exists(script):
            os.chmod(script, 0o755)
            print(f"✅ Made {script} executable")


def validate_workflow_configuration():
    """Validate that workflow steps match available agents."""
    try:
        workflow_steps = json.loads('{{ cookiecutter.workflow_steps_json }}')
        specialist_agents = json.loads('{{ cookiecutter.specialist_agents_json }}')
        
        agent_names = {agent['name'] for agent in specialist_agents}
        
        for step in workflow_steps:
            if step['agent'] not in agent_names:
                print(f"⚠️  Warning: Step '{step['name']}' references agent '{step['agent']}' which is not in specialist_agents")
    except Exception as e:
        print(f"⚠️  Warning: Could not validate workflow configuration: {e}")


def initialize_git():
    """Initialize git repository."""
    try:
        subprocess.run(['git', 'init'], check=True, capture_output=True)
        subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit from workflow supervisor template'], 
                      check=True, capture_output=True)
        print("✅ Initialized git repository")
    except subprocess.CalledProcessError:
        print("⚠️  Could not initialize git repository (git may not be installed)")
    except Exception as e:
        print(f"⚠️  Git initialization failed: {e}")


def print_workflow_summary():
    """Print a summary of the workflow configuration."""
    try:
        workflow_steps = json.loads('{{ cookiecutter.workflow_steps_json }}')
        specialist_agents = json.loads('{{ cookiecutter.specialist_agents_json }}')
        
        print("\n📋 Workflow Configuration Summary:")
        print(f"   Strategy: {{ cookiecutter.supervisor_strategy }}")
        print(f"   Error Handling: {{ cookiecutter.error_handling }}")
        print(f"   Total Steps: {len(workflow_steps)}")
        print(f"   Total Agents: {len(specialist_agents)}")
        
        print("\n   Workflow Steps:")
        for step in workflow_steps:
            print(f"     - {step['name']}: {step.get('description', 'No description')} (agent: {step['agent']})")
        
        print("\n   Specialist Agents:")
        for agent in specialist_agents:
            print(f"     - {agent['name']}: {agent.get('description', 'No description')}")
            print(f"       Endpoint: {agent['endpoint']}")
    except Exception as e:
        print(f"⚠️  Could not print workflow summary: {e}")


def print_next_steps():
    """Print helpful next steps for the user."""
    project_slug = '{{ cookiecutter.project_slug }}'
    domain = '{{ cookiecutter.domain }}'
    
    print("\n" + "="*60)
    print(f"🎉 Successfully generated workflow supervisor: {project_slug}")
    print("="*60)
    print("\n📋 Next Steps:\n")
    print(f"1. cd {project_slug}")
    print("2. npm install")
    print("3. cp .env.local.example .env.local")
    print("4. Edit .env.local with your Cloudflare credentials")
    print("5. Configure specialist agents in wrangler.toml")
    print("6. npx wrangler dev  # Run locally")
    print("\n🚀 Deploy to production:")
    print("   export CLOUDFLARE_API_TOKEN='your-token'")
    print("   ./scripts/deploy.sh")
    print(f"\n🌐 Domain: https://{domain}")
    print("\n🔧 Workflow Features:")
    print("   - Multi-agent orchestration")
    print("   - State management and persistence")
    print("   - Error handling and retries")
    print("   - Progress tracking")
    print("   - MCP protocol support")
    print("   - LangChain.js integration")
    print("\n📖 For more information, see README.md")
    print("="*60 + "\n")


def create_env_example():
    """Create .env.local.example file."""
    env_content = """# Cloudflare API Token for deployment
CLOUDFLARE_API_TOKEN=your_api_token_here

# Optional: Cloudflare Account ID
CLOUDFLARE_ACCOUNT_ID=your_account_id_here

# Optional: KV Namespace ID for workflow state
KV_NAMESPACE_ID=your_kv_namespace_id_here

# Specialist Agent Endpoints (update with your actual endpoints)
"""
    
    try:
        agents = json.loads('{{ cookiecutter.specialist_agents_json }}')
        for agent in agents:
            env_content += f"# {agent['name'].upper()}_ENDPOINT={agent['endpoint']}\n"
    except:
        pass
    
    with open('.env.local.example', 'w') as f:
        f.write(env_content)
    print("✅ Created .env.local.example")


def main():
    """Run post-generation tasks."""
    make_scripts_executable()
    validate_workflow_configuration()
    create_env_example()
    initialize_git()
    print_workflow_summary()
    print_next_steps()


if __name__ == '__main__':
    main()