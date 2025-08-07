# Cookiecutter Migration Plan for Agentopia

## Overview

This document outlines the comprehensive plan to migrate the Agentopia framework from its current string-based templating system to a cookiecutter-based approach with individual GitHub repositories for each template.

## Current State Analysis

### JavaScript Templates (generators/javascript/)
- **Router Agent**: Routes requests to specialist agents with pattern matching
- **Specialist Agent**: Domain-specific agents with MCP tool integration
- **LangGraph Patterns** (7 types):
  - Supervisor: Manages multiple specialized agents
  - Network: Distributed agent collaboration
  - Hierarchical: Multi-level agent organization
  - Committee: Consensus-based decisions
  - Reflection: Self-improving agents
  - Pipeline: Sequential processing
  - Autonomous: Self-directed agents

### Python Templates (generators/python/)
- Partial cookiecutter implementation exists but not actively used
- Same agent types as JavaScript but incomplete LangGraph patterns
- Uses FFI imports for Cloudflare Workers compatibility

## Repository Naming Convention

Format: `cc-{language}-{type}-{name}`

### Planned Repositories

#### JavaScript Templates
1. `cc-js-router-agent` - Router agent template
2. `cc-js-specialist-agent` - Specialist agent template
3. `cc-js-workflow-supervisor` - LangGraph supervisor pattern
4. `cc-js-workflow-network` - LangGraph network pattern
5. `cc-js-workflow-hierarchical` - LangGraph hierarchical pattern
6. `cc-js-workflow-committee` - LangGraph committee pattern
7. `cc-js-workflow-reflection` - LangGraph reflection pattern
8. `cc-js-workflow-pipeline` - LangGraph pipeline pattern
9. `cc-js-workflow-autonomous` - LangGraph autonomous pattern

#### Python Templates
1. `cc-py-router-agent` - Router agent template
2. `cc-py-specialist-agent` - Specialist agent template
3. `cc-py-workflow-supervisor` - LangGraph supervisor pattern
4. `cc-py-workflow-network` - LangGraph network pattern
5. `cc-py-workflow-hierarchical` - LangGraph hierarchical pattern
6. `cc-py-workflow-committee` - LangGraph committee pattern
7. `cc-py-workflow-reflection` - LangGraph reflection pattern
8. `cc-py-workflow-pipeline` - LangGraph pipeline pattern
9. `cc-py-workflow-autonomous` - LangGraph autonomous pattern

## Migration Strategy

### Phase 1: Repository Creation and Basic Structure
1. Create GitHub repositories for each template
2. Initialize with cookiecutter structure
3. Add basic README and Makefile
4. Set up GitHub Actions for CI/CD

### Phase 2: Template Migration
1. Extract template content from current string-based system
2. Convert to cookiecutter template format
3. Define cookiecutter.json variables
4. Add pre/post generation hooks where needed

### Phase 3: Documentation and Testing
1. Write comprehensive README for each template
2. Add implementation notes and caveats
3. Create example configurations
4. Test template generation

### Phase 4: Update Agent Builders
1. Modify JavaScript agent-builder.js to use cookiecutter
2. Modify Python agent_builder.py to use cookiecutter
3. Update configuration handling
4. Add template repository management

## Template Structure

Each cookiecutter repository will follow this structure:

```
cc-{lang}-{type}-{name}/
├── cookiecutter.json              # Template variables
├── {{cookiecutter.project_slug}}/
│   ├── src/
│   │   └── index.js/py           # Main agent code
│   ├── scripts/
│   │   └── deploy-all.sh         # Deployment script
│   ├── .github/
│   │   └── workflows/
│   │       └── deploy.yml        # GitHub Actions CI/CD
│   ├── wrangler.toml             # Cloudflare config
│   ├── package.json/pyproject.toml
│   ├── README.md                 # Generated project docs
│   ├── .env.local.example
│   └── .gitignore
├── hooks/
│   ├── pre_gen_project.py        # Validation
│   └── post_gen_project.py       # Setup tasks
├── README.md                      # Template documentation
├── Makefile                       # Template management
└── LICENSE
```

## Cookiecutter Variables

Common variables across all templates:
```json
{
  "project_name": "My Agent",
  "project_slug": "{{ cookiecutter.project_name.lower().replace(' ', '-') }}",
  "description": "A Cloudflare Workers agent",
  "author_name": "Your Name",
  "domain": "example.com",
  "cloudflare_account_id": "",
  "cloudflare_zone_id": "",
  "ai_model": "@cf/meta/llama-3-70b-instruct",
  "max_tokens": 1000,
  "temperature": 0.7,
  "cache_enabled": "true",
  "cache_ttl": 3600,
  "system_prompt": "You are a helpful assistant.",
  "use_langchain": "true"
}
```

Additional variables for specific templates:
- Router: `registry_tools` (JSON array)
- Specialist: `mcp_tool_name`, `keywords`, `patterns`, `expertise`
- LangGraph: `pattern_type`, `max_iterations`, `agents` (for multi-agent patterns)

## Implementation Timeline

### Week 1: Foundation ✅ COMPLETE
- [x] Create migration tracking in TODO.md
- [x] Set up first 3 repositories (router and specialist for both languages)
- [x] Implement basic cookiecutter structure for cc-js-router-agent
- [x] Test basic generation - cc-js-router-agent working!
- [x] Complete cc-js-specialist-agent - Working with all features!
- [x] Complete cc-py-router-agent - Python support ready!

### Week 2: Core Templates
- [ ] Migrate router and specialist templates
- [ ] Add documentation and Makefiles
- [ ] Set up GitHub Actions
- [ ] Test end-to-end deployment

### Week 3: LangGraph Patterns
- [ ] Create repositories for all LangGraph patterns
- [ ] Migrate supervisor and network patterns first
- [ ] Continue with remaining patterns
- [ ] Ensure JavaScript/Python parity

### Week 4: Integration and Testing
- [ ] Update agent builders to use cookiecutter
- [ ] Create template registry/discovery mechanism
- [ ] Comprehensive testing
- [ ] Update main project documentation

## Success Criteria

1. All templates migrated to individual cookiecutter repositories
2. GitHub Actions CI/CD working for generated projects
3. Agent builders updated to use cookiecutter templates
4. Documentation complete with implementation notes
5. Templates testable independently
6. Consistent structure across JavaScript and Python

## Risks and Mitigation

1. **Risk**: Breaking existing functionality
   - **Mitigation**: Keep old system working during migration, switch over only when ready

2. **Risk**: Template version management complexity
   - **Mitigation**: Use GitHub releases and tags for versioning

3. **Risk**: Python Pyodide compatibility issues
   - **Mitigation**: Test thoroughly with Cloudflare Workers Python runtime

4. **Risk**: Increased complexity for users
   - **Mitigation**: Provide clear documentation and helper scripts

## Post-Migration Benefits

1. Cleaner separation of concerns
2. Easier template maintenance and updates
3. Better version control for templates
4. Independent testing of templates
5. Community contribution potential
6. Professional structure following cookiecutter best practices

## Lessons Learned (Week 1)

1. **GitHub API Authentication**: MCP GitHub tool may use different token than environment
2. **Cookiecutter Limitations**: Arrays must be JSON strings, no complex expressions
3. **Template Conflicts**: Framework code with `{{` needs escaping
4. **Post-Generation Hooks**: Essential for computing derived values
5. **Testing Strategy**: Use Makefile with `test` target for quick validation

See [COOKIECUTTER_GUIDE.md](COOKIECUTTER_GUIDE.md) for detailed lessons and solutions.

## Next Steps

1. ~~Review and approve this migration plan~~ ✅
2. ~~Create first repository as proof of concept~~ ✅ cc-js-router-agent complete
3. Iterate based on learnings - In progress
4. Execute full migration - Week 2-4

---

This is a living document and will be updated as the migration progresses.