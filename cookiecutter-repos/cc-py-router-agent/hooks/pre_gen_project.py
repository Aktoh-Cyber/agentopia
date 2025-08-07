#!/usr/bin/env python
"""Pre-generation hook for Python router template."""

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


def validate_json_object(json_str, field_name):
    """Validate that a string is a valid JSON object."""
    try:
        data = json.loads(json_str)
        if not isinstance(data, dict):
            print(f"ERROR: {field_name} must be a JSON object")
            sys.exit(1)
        return True
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {field_name}: {e}")
        sys.exit(1)


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


def main():
    """Run pre-generation validations."""
    domain = '{{cookiecutter.domain}}'
    registry_json = '{{cookiecutter.registry_json}}'
    examples_json = '{{cookiecutter.examples_json}}'
    
    # Run validations
    validate_domain(domain)
    validate_json_object(registry_json, 'registry_json')
    validate_json_array(examples_json, 'examples_json')
    
    print("✅ All validations passed for Python router!")


if __name__ == '__main__':
    main()