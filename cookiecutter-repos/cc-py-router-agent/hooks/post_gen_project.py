#!/usr/bin/env python
"""Post-generation hook for Python router template."""

import os
import subprocess
from datetime import datetime


def make_scripts_executable():
    """Make deployment scripts executable."""
    scripts = ['scripts/deploy.sh']
    for script in scripts:
        if os.path.exists(script):
            os.chmod(script, 0o755)
            print(f"✅ Made {script} executable")


def initialize_git():
    """Initialize git repository."""
    try:
        subprocess.run(['git', 'init'], check=True, capture_output=True)
        subprocess.run(['git', 'add', '.'], check=True, capture_output=True)
        subprocess.run(['git', 'commit', '-m', 'Initial commit from Python router template'], 
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
    
    print("\n" + "="*60)
    print(f"🎉 Successfully generated Python router agent: {project_slug}")
    print("="*60)
    print("\n📋 Next Steps:\n")
    print(f"1. cd {project_slug}")
    print("2. pip install -e .[dev]  # Install dev dependencies")
    print("3. npm install -g wrangler  # Install Wrangler CLI")
    print("4. cp .env.local.example .env.local")
    print("5. Edit .env.local with your Cloudflare credentials")
    print("6. npx wrangler dev  # Run locally")
    print("\n🚀 Deploy to production:")
    print("   export CLOUDFLARE_API_TOKEN='your-token'")
    print("   ./scripts/deploy.sh")
    print(f"\n🌐 Domain: https://{domain}")
    print("\n🐍 Python Notes:")
    print("   - Production uses standard library only")
    print("   - Development can use any Python packages")
    print("   - FFI imports available: from js import fetch, console")
    print("   - Full async/await support")
    print("\n📖 For adding specialist agents, see README.md")
    print("="*60 + "\n")


def main():
    """Run post-generation tasks."""
    make_scripts_executable()
    initialize_git()
    print_next_steps()


if __name__ == '__main__':
    main()