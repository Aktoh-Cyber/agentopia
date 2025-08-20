#!/usr/bin/env python
"""Pre-generation hook for Python workflow supervisor template."""

import re
import sys
import json


def validate_domain(domain):
    """Validate domain format."""
    # Allow localhost for development
    if domain == 'localhost' or domain.startswith('localhost:'):
        return True
    
    # Check for valid domain pattern
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-]*\.([a-zA-Z0-9][a-zA-Z0-9-]*\.)*[a-zA-Z]{2,}$'
    if not re.match(pattern, domain):
        print(f"ERROR: Invalid domain format: {domain}")
        print("Domain should be like: example.com or sub.example.com")
        sys.exit(1)
    return True


def validate_json_array(json_str, field_name):
    """Validate that a string is a valid JSON array."""
    try:
        data = json.loads(json_str)
        if not isinstance(data, list):
            print(f"ERROR: {field_name} must be a JSON array")
            sys.exit(1)
        return True
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {field_name}: {e}")
        sys.exit(1)


def validate_supervisor_strategy(strategy):
    """Validate supervisor strategy."""
    valid_strategies = ['sequential', 'parallel', 'conditional', 'map_reduce']
    if strategy not in valid_strategies:
        print(f"ERROR: Invalid supervisor strategy: {strategy}")
        print(f"Valid strategies are: {', '.join(valid_strategies)}")
        sys.exit(1)
    return True


def validate_error_handling(handling):
    """Validate error handling strategy."""
    valid_strategies = ['retry_with_fallback', 'circuit_breaker', 'compensate']
    if handling not in valid_strategies:
        print(f"ERROR: Invalid error handling: {handling}")
        print(f"Valid strategies are: {', '.join(valid_strategies)}")
        sys.exit(1)
    return True


def validate_workflow_steps(steps_json):
    """Validate workflow steps structure."""
    try:
        steps = json.loads(steps_json)
        if not isinstance(steps, list):
            print("ERROR: workflow_steps_json must be a JSON array")
            sys.exit(1)
        
        for i, step in enumerate(steps):
            if not isinstance(step, dict):
                print(f"ERROR: Workflow step {i} must be an object")
                sys.exit(1)
            
            if 'name' not in step:
                print(f"ERROR: Workflow step {i} missing 'name' field")
                sys.exit(1)
            
            if 'agent' not in step:
                print(f"ERROR: Workflow step {i} missing 'agent' field")
                sys.exit(1)
        
        return True
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in workflow_steps_json: {e}")
        sys.exit(1)


def validate_specialist_agents(agents_json):
    """Validate specialist agents structure."""
    try:
        agents = json.loads(agents_json)
        if not isinstance(agents, list):
            print("ERROR: specialist_agents_json must be a JSON array")
            sys.exit(1)
        
        for i, agent in enumerate(agents):
            if not isinstance(agent, dict):
                print(f"ERROR: Specialist agent {i} must be an object")
                sys.exit(1)
            
            if 'name' not in agent:
                print(f"ERROR: Specialist agent {i} missing 'name' field")
                sys.exit(1)
            
            if 'endpoint' not in agent:
                print(f"ERROR: Specialist agent {i} missing 'endpoint' field")
                sys.exit(1)
        
        return True
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in specialist_agents_json: {e}")
        sys.exit(1)


def validate_python_compatibility():
    """Validate Python compatibility for Pyodide runtime."""
    print("Validating Python Pyodide compatibility...")
    
    # Check Python version (should work with Python 3.9+)
    python_version = sys.version_info
    if python_version.major < 3 or (python_version.major == 3 and python_version.minor < 9):
        print("WARNING: Python 3.9+ recommended for Pyodide compatibility")
    
    return True


def validate_agent_class_name(class_name):
    """Validate agent class name."""
    # Must be valid Python identifier
    if not class_name.isidentifier():
        print(f"ERROR: agent_class_name '{class_name}' is not a valid Python identifier")
        sys.exit(1)
    
    # Should be PascalCase
    if not class_name[0].isupper():
        print(f"WARNING: agent_class_name '{class_name}' should start with uppercase letter")
    
    return True


def main():
    """Run pre-generation validations."""
    domain = '{{ cookiecutter.domain }}'
    workflow_steps_json = '{{ cookiecutter.workflow_steps_json }}'
    specialist_agents_json = '{{ cookiecutter.specialist_agents_json }}'
    supervisor_strategy = '{{ cookiecutter.supervisor_strategy }}'
    error_handling = '{{ cookiecutter.error_handling }}'
    agent_class_name = '{{ cookiecutter.agent_class_name }}'
    
    print("🐍 Validating Python workflow supervisor template...")
    
    # Run validations
    validate_domain(domain)
    validate_supervisor_strategy(supervisor_strategy)
    validate_error_handling(error_handling)
    validate_workflow_steps(workflow_steps_json)
    validate_specialist_agents(specialist_agents_json)
    validate_agent_class_name(agent_class_name)
    validate_python_compatibility()
    
    # Validate numeric fields
    try:
        max_retries = int('{{ cookiecutter.max_retries }}')
        if max_retries < 0 or max_retries > 10:
            print(f"ERROR: max_retries should be between 0 and 10")
            sys.exit(1)
    except ValueError:
        print("ERROR: max_retries must be a number")
        sys.exit(1)
    
    try:
        timeout_ms = int('{{ cookiecutter.timeout_ms }}')
        if timeout_ms < 1000 or timeout_ms > 300000:
            print(f"ERROR: timeout_ms should be between 1000 and 300000 (1s to 5min)")
            sys.exit(1)
    except ValueError:
        print("ERROR: timeout_ms must be a number")
        sys.exit(1)
    
    try:
        max_tokens = int('{{ cookiecutter.max_tokens }}')
        if max_tokens < 100 or max_tokens > 4096:
            print(f"ERROR: max_tokens should be between 100 and 4096")
            sys.exit(1)
    except ValueError:
        print("ERROR: max_tokens must be a number")
        sys.exit(1)
    
    try:
        temperature = float('{{ cookiecutter.temperature }}')
        if temperature < 0.0 or temperature > 2.0:
            print(f"ERROR: temperature should be between 0.0 and 2.0")
            sys.exit(1)
    except ValueError:
        print("ERROR: temperature must be a number")
        sys.exit(1)
    
    try:
        cache_ttl = int('{{ cookiecutter.cache_ttl }}')
        if cache_ttl < 0 or cache_ttl > 86400:
            print(f"ERROR: cache_ttl should be between 0 and 86400 seconds (24 hours)")
            sys.exit(1)
    except ValueError:
        print("ERROR: cache_ttl must be a number")
        sys.exit(1)
    
    # Validate AI model format
    ai_model = '{{ cookiecutter.ai_model }}'
    if not ai_model.startswith('@cf/'):
        print("WARNING: AI model should start with '@cf/' for Cloudflare Workers AI")
    
    # Cross-validate workflow steps and agents
    try:
        steps = json.loads(workflow_steps_json)
        agents = json.loads(specialist_agents_json)
        
        agent_names = {agent['name'] for agent in agents}
        
        for step in steps:
            if step['agent'] not in agent_names:
                print(f"ERROR: Step '{step['name']}' references unknown agent '{step['agent']}'")
                sys.exit(1)
        
    except json.JSONDecodeError:
        # Already handled in individual validation functions
        pass
    
    print("✅ All validations passed for Python workflow supervisor!")
    print("🎯 Ready to generate Pyodide-compatible workflow supervisor")
    print("🔧 Features enabled:")
    print("   - Multi-agent orchestration")
    print("   - State management with KV storage")
    print("   - Error handling and retries")
    print("   - MCP protocol support")
    print("   - FFI integration with Cloudflare Workers")


if __name__ == '__main__':
    main()