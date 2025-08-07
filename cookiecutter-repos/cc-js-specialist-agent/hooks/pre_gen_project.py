#!/usr/bin/env python
"""Pre-generation hook for cookiecutter."""

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

def validate_mcp_tool_name(name):
    """Validate MCP tool name format."""
    pattern = r'^[a-zA-Z][a-zA-Z0-9_]*$'
    if not re.match(pattern, name):
        print(f"ERROR: Invalid MCP tool name: {name}")
        print("Tool name should start with a letter and contain only letters, numbers, and underscores")
        sys.exit(1)
    return True

def main():
    """Run pre-generation validations."""
    domain = '{{cookiecutter.domain}}'
    mcp_tool_name = '{{cookiecutter.mcp_tool_name}}'
    keywords_json = '{{cookiecutter.keywords_json}}'
    patterns_json = '{{cookiecutter.patterns_json}}'
    examples_json = '{{cookiecutter.examples_json}}'
    
    # Run validations
    validate_domain(domain)
    validate_mcp_tool_name(mcp_tool_name)
    validate_json_array(keywords_json, 'keywords_json')
    validate_json_array(patterns_json, 'patterns_json')
    validate_json_array(examples_json, 'examples_json')
    
    print("✅ All validations passed!")

if __name__ == '__main__':
    main()