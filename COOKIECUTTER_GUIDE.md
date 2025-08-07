# Cookiecutter Template Development Guide

This guide documents lessons learned from creating cookiecutter templates for the Agentopia framework.

## Key Lessons Learned

### 1. GitHub Repository Creation

#### Required Permissions
- Personal Access Token (PAT) needs these scopes:
  - `repo` - Full control of private repositories
  - `admin:org` or `write:org` - Organization repository creation
  
#### Organization Repository Creation
```bash
# Via API (requires proper token scopes)
curl -X POST -H "Authorization: token $GITHUB_PERSONAL_ACCESS_TOKEN" \
     -H "Accept: application/vnd.github.v3+json" \
     https://api.github.com/orgs/ORGNAME/repos \
     -d '{"name":"repo-name","private":true,"auto_init":true}'
```

### 2. Cookiecutter Variable Limitations

#### Arrays and Complex Types
- **Problem**: Cookiecutter treats arrays as choice fields
- **Solution**: Use JSON strings for complex data
```json
// Instead of:
"examples": ["example1", "example2"]

// Use:
"examples_json": "[\"example1\", \"example2\"]"
```

#### Computed Values
- **Problem**: Cookiecutter doesn't support complex expressions like `.split()`
- **Solution**: Use post-generation hooks to compute values
```python
# hooks/post_gen_project.py
domain = '{{cookiecutter.domain}}'
subdomain = domain.split('.')[0] if '.' in domain else domain
```

### 3. Template Conflicts

#### Jinja2 Pattern Conflicts
- **Problem**: Code containing `{{` or `}}` conflicts with Jinja2
- **Solution**: Escape or modify patterns in framework files
```bash
# Replace {{ with {__{ and }} with }__}
sed -i '' 's/{{/{__{/g; s/}}/}__}/g' file.js
```

### 4. Project Structure

#### Recommended Template Structure
```
cc-{lang}-{type}-{name}/
├── cookiecutter.json          # Template variables
├── hooks/
│   ├── pre_gen_project.py    # Validation
│   └── post_gen_project.py   # Setup & computed values
├── {{cookiecutter.project_slug}}/
│   ├── src/                  # Source code
│   ├── scripts/               # Deployment scripts
│   ├── .github/workflows/     # CI/CD
│   └── README.md             # Project docs
├── README.md                  # Template documentation
├── Makefile                   # Template management
└── .gitignore                # Ignore test outputs
```

### 5. Testing Templates

#### Basic Test Command
```makefile
test:
	@rm -rf test-output
	@cookiecutter . --no-input --output-dir test-output
	@cd test-output/* && npm install
```

#### Common Issues and Fixes
1. **IndexError: list index out of range**
   - Cause: Array being treated as choice field
   - Fix: Convert to JSON string

2. **'OrderedDict object' has no attribute**
   - Cause: Variable name mismatch
   - Fix: Ensure all template variables match cookiecutter.json

3. **TemplateSyntaxError**
   - Cause: Conflicting patterns in template files
   - Fix: Escape conflicting patterns

### 6. Pre/Post Generation Hooks

#### Pre-generation (validation)
```python
def validate_domain(domain):
    pattern = r'^[a-zA-Z0-9][a-zA-Z0-9-]*\.([a-zA-Z0-9][a-zA-Z0-9-]*\.)*[a-zA-Z]{2,}$'
    if not re.match(pattern, domain):
        print(f"ERROR: Invalid domain format: {domain}")
        sys.exit(1)
```

#### Post-generation (computed values)
```python
def process_templates():
    # Compute values
    agent_class_name = ''.join(project_name.split())
    
    # Update files
    replacements = {
        '{{cookiecutter.agent_class_name}}': agent_class_name
    }
    
    for filepath in files_to_update:
        with open(filepath, 'r') as f:
            content = f.read()
        for old, new in replacements.items():
            content = content.replace(old, new)
        with open(filepath, 'w') as f:
            f.write(content)
```

### 7. GitHub Actions Integration

#### Template Variables in Workflows
Use double curly braces with spaces for GitHub Actions variables:
```yaml
apiToken: ${{ '{{' }} secrets.CLOUDFLARE_API_TOKEN {{ '}}' }}
```

### 8. Repository Naming Convention

Format: `cc-{language}-{type}-{name}`

Examples:
- `cc-js-router-agent`
- `cc-js-specialist-agent`
- `cc-py-workflow-supervisor`

### 9. Documentation Best Practices

#### In Template README
- Clear installation instructions
- Configuration variable table
- Customization points
- Troubleshooting section

#### In Generated Project README
- Placeholder for user documentation
- Implementation notes section
- Clear markers for where to add custom docs

### 10. Makefile for Template Management

Essential targets:
```makefile
help:    # Show available commands
test:    # Test template generation
clean:   # Remove test artifacts
push:    # Push to GitHub
```

## Migration Strategy

1. **Phase 1**: Create repositories and basic structure
2. **Phase 2**: Migrate templates from string-based system
3. **Phase 3**: Add documentation and testing
4. **Phase 4**: Update builders to use cookiecutter

## Next Steps

1. Complete remaining templates (specialist, Python versions)
2. Update agent builders to use cookiecutter
3. Add template versioning strategy
4. Create template registry/discovery mechanism
5. Add automated testing for all templates

## Resources

- [Cookiecutter Documentation](https://cookiecutter.readthedocs.io/)
- [Jinja2 Template Documentation](https://jinja.palletsprojects.com/)
- [GitHub API Documentation](https://docs.github.com/en/rest)

---

*This guide is based on the migration of Agentopia framework to cookiecutter templates.*