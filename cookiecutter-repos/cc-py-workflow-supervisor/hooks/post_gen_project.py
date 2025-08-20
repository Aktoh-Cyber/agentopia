#!/usr/bin/env python
"""Post-generation hook for Python workflow supervisor template."""

import os
import subprocess
import json
import sys


def make_scripts_executable():
    """Make deployment scripts executable."""
    scripts = ['scripts/deploy.sh']
    for script in scripts:
        if os.path.exists(script):
            os.chmod(script, 0o755)
            print(f"✅ Made {script} executable")


def validate_python_files():
    """Validate generated Python files."""
    python_files = [
        'src/entry.py',
        'src/base_agent.py',
        'src/workflow_engine.py',
        'src/state_manager.py'
    ]
    
    print("🐍 Validating generated Python files...")
    
    for py_file in python_files:
        if os.path.exists(py_file):
            try:
                # Check syntax by compiling
                with open(py_file, 'r') as f:
                    compile(f.read(), py_file, 'exec')
                print(f"✅ {py_file} syntax is valid")
            except SyntaxError as e:
                print(f"❌ Syntax error in {py_file}: {e}")
                sys.exit(1)
        else:
            print(f"❌ Missing required file: {py_file}")
            sys.exit(1)


def validate_workflow_configuration():
    """Validate that workflow steps match available agents."""
    try:
        workflow_steps = json.loads('{{ cookiecutter.workflow_steps_json }}')
        specialist_agents = json.loads('{{ cookiecutter.specialist_agents_json }}')
        
        agent_names = {agent['name'] for agent in specialist_agents}
        
        print("🔧 Validating workflow configuration...")
        
        for step in workflow_steps:
            if step['agent'] not in agent_names:
                print(f"⚠️  Warning: Step '{step['name']}' references agent '{step['agent']}' which is not in specialist_agents")
            else:
                print(f"✅ Step '{step['name']}' -> Agent '{step['agent']}' mapping is valid")
                
    except Exception as e:
        print(f"⚠️  Warning: Could not validate workflow configuration: {e}")


def check_pyodide_compatibility():
    """Check for potential Pyodide compatibility issues."""
    print("🔬 Checking Pyodide compatibility...")
    
    # List of Python features that might need attention in Pyodide
    warnings = []
    
    # Check for file operations that might not work in Workers
    for root, dirs, files in os.walk('src'):
        for file in files:
            if file.endswith('.py'):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r') as f:
                        content = f.read()
                        
                        # Check for potentially problematic imports
                        if 'import threading' in content or 'from threading' in content:
                            warnings.append(f"{filepath}: Threading may have limitations in Pyodide")
                        
                        if 'import multiprocessing' in content or 'from multiprocessing' in content:
                            warnings.append(f"{filepath}: Multiprocessing not available in Pyodide")
                        
                        if 'import subprocess' in content or 'from subprocess' in content:
                            warnings.append(f"{filepath}: Subprocess not available in Pyodide")
                        
                except Exception as e:
                    print(f"⚠️  Could not check {filepath}: {e}")
    
    if warnings:
        print("⚠️  Potential Pyodide compatibility issues:")
        for warning in warnings:
            print(f"    {warning}")
    else:
        print("✅ No obvious Pyodide compatibility issues found")


def initialize_git():
    """Initialize git repository."""
    try:
        subprocess.run(['git', 'init'], check=True, capture_output=True)
        
        # Create .gitignore for Python projects
        gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Environment variables
.env
.env.local
.env.production

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Wrangler
.wrangler/
wrangler.toml.bak

# Logs
*.log
logs/

# Cache
.cache/
"""
        
        with open('.gitignore', 'w') as f:
            f.write(gitignore_content)
        
        subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit from Python workflow supervisor template'], 
                      check=True, capture_output=True)
        print("✅ Initialized git repository with Python .gitignore")
    except subprocess.CalledProcessError:
        print("⚠️  Could not initialize git repository (git may not be installed)")
    except Exception as e:
        print(f"⚠️  Git initialization failed: {e}")


def print_workflow_summary():
    """Print a summary of the workflow configuration."""
    try:
        workflow_steps = json.loads('{{ cookiecutter.workflow_steps_json }}')
        specialist_agents = json.loads('{{ cookiecutter.specialist_agents_json }}')
        
        print("\n📋 Python Workflow Configuration Summary:")
        print(f"   Runtime: Pyodide on Cloudflare Workers")
        print(f"   Strategy: {{ cookiecutter.supervisor_strategy }}")
        print(f"   Error Handling: {{ cookiecutter.error_handling }}")
        print(f"   Total Steps: {len(workflow_steps)}")
        print(f"   Total Agents: {len(specialist_agents)}")
        print(f"   AI Model: {{ cookiecutter.ai_model }}")
        print(f"   Max Retries: {{ cookiecutter.max_retries }}")
        print(f"   Timeout: {{ cookiecutter.timeout_ms }}ms")
        
        print("\n   🔄 Workflow Steps:")
        for step in workflow_steps:
            print(f"     - {step['name']}: {step.get('description', 'No description')} (agent: {step['agent']})")
        
        print("\n   🤖 Specialist Agents:")
        for agent in specialist_agents:
            print(f"     - {agent['name']}: {agent.get('description', 'No description')}")
            print(f"       Endpoint: {agent['endpoint']}")
            
    except Exception as e:
        print(f"⚠️  Could not print workflow summary: {e}")


def create_requirements_dev():
    """Create requirements-dev.txt for local development."""
    requirements_content = """# Development dependencies for Python workflow supervisor
# Note: Production uses Pyodide runtime with standard library only

# Code quality
black>=22.0.0
mypy>=1.0.0
flake8>=6.0.0

# Testing
pytest>=7.0.0
pytest-asyncio>=0.21.0

# Development tools
ipython>=8.0.0

# Type stubs for FFI imports (development only)
types-requests>=2.28.0
"""
    
    with open('requirements-dev.txt', 'w') as f:
        f.write(requirements_content)
    print("✅ Created requirements-dev.txt for local development")


def create_env_example():
    """Create .env.local.example file."""
    env_content = """# Cloudflare API Token for deployment
CLOUDFLARE_API_TOKEN=your_api_token_here

# Optional: Cloudflare Account ID
CLOUDFLARE_ACCOUNT_ID={{ cookiecutter.cloudflare_account_id or 'your_account_id_here' }}

# Optional: Cloudflare Zone ID
CLOUDFLARE_ZONE_ID={{ cookiecutter.cloudflare_zone_id or 'your_zone_id_here' }}

# Optional: KV Namespace ID for workflow state
KV_NAMESPACE_ID=your_kv_namespace_id_here

# Development settings
DEBUG=true
ENVIRONMENT=development

# AI Configuration
AI_MODEL={{ cookiecutter.ai_model }}
MAX_TOKENS={{ cookiecutter.max_tokens }}
TEMPERATURE={{ cookiecutter.temperature }}

# Workflow Configuration
SUPERVISOR_STRATEGY={{ cookiecutter.supervisor_strategy }}
ERROR_HANDLING={{ cookiecutter.error_handling }}
MAX_RETRIES={{ cookiecutter.max_retries }}
TIMEOUT_MS={{ cookiecutter.timeout_ms }}

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


def create_development_readme():
    """Create a development-specific README section."""
    readme_section = """

## Python Development Notes

### Pyodide Runtime
This workflow supervisor runs on Cloudflare Workers using the Pyodide Python runtime. Key considerations:

- **Standard Library Only**: Production uses only Python standard library for maximum compatibility
- **FFI Integration**: JavaScript APIs accessed via `from js import` statements
- **Third-party Packages**: Supported via Pywrangler bundling (WebAssembly compatible packages only)

### Local Development
```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Code formatting
python -m black src/

# Type checking
python -m mypy src/

# Syntax validation
python -m py_compile src/*.py
```

### Deployment Requirements
- Python 3.9+ (for Pyodide compatibility)
- Wrangler CLI (`npm install -g wrangler`)
- Cloudflare API token with Workers permissions

### FFI Integration Examples
```python
# Cloudflare Workers API access
from js import console, fetch, Response

# Crypto utilities
from js import crypto as js_crypto
uuid = js_crypto.randomUUID()

# JSON utilities
from js import JSON as js_json
data = js_json.parse(json_string)
```

### Performance Optimization
- Use standard library implementations where possible
- Minimize FFI calls in hot paths
- Leverage async/await for I/O operations
- Cache frequently accessed data in memory

"""
    
    # Append to README if it exists
    if os.path.exists('README.md'):
        with open('README.md', 'a') as f:
            f.write(readme_section)
        print("✅ Added Python development section to README.md")


def print_next_steps():
    """Print helpful next steps for the user."""
    project_slug = '{{ cookiecutter.project_slug }}'
    domain = '{{ cookiecutter.domain }}'
    
    print("\n" + "="*70)
    print(f"🐍 Successfully generated Python workflow supervisor: {project_slug}")
    print("="*70)
    print("\n📋 Next Steps:\n")
    print(f"1. cd {project_slug}")
    print("2. pip install -r requirements-dev.txt  # For local development")
    print("3. cp .env.local.example .env.local")
    print("4. Edit .env.local with your Cloudflare credentials")
    print("5. Configure specialist agents in wrangler.toml")
    print("6. wrangler dev  # Run locally with Pyodide")
    print("\n🚀 Deploy to production:")
    print("   export CLOUDFLARE_API_TOKEN='your-token'")
    print("   ./scripts/deploy.sh")
    print("\n🔧 Set up KV storage:")
    print("   ./scripts/deploy.sh --setup-kv")
    print(f"\n🌐 Domain: https://{domain}")
    print("\n🐍 Python Features:")
    print("   - Pyodide runtime for maximum compatibility")
    print("   - FFI integration with Cloudflare Workers APIs")
    print("   - Standard library only (production)")
    print("   - Async/await throughout")
    print("   - Type hints for better development experience")
    print("   - Multi-agent workflow orchestration")
    print("   - State management with KV persistence")
    print("   - Error handling and retry strategies")
    print("   - MCP protocol support")
    print("\n⚠️  Important Notes:")
    print("   - Test thoroughly in local Pyodide environment")
    print("   - Standard library only in production")
    print("   - Use FFI imports for Cloudflare Workers APIs")
    print("   - Third-party packages via Pywrangler (WebAssembly compatible)")
    print("\n📖 For more information, see README.md")
    print("="*70 + "\n")


def main():
    """Run post-generation tasks."""
    print("🎯 Running post-generation tasks for Python workflow supervisor...")
    
    make_scripts_executable()
    validate_python_files()
    validate_workflow_configuration()
    check_pyodide_compatibility()
    create_requirements_dev()
    create_env_example()
    initialize_git()
    create_development_readme()
    print_workflow_summary()
    print_next_steps()


if __name__ == '__main__':
    main()