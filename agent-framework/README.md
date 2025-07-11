# Multi-Language Agent Framework

A modular framework for building and deploying AI agents on Cloudflare Workers with intelligent routing and MCP (Model Context Protocol) support. Now supports both **JavaScript** and **Python** implementations!

## 🚀 Overview

This framework enables rapid development of specialized AI agents that can work together through a router-agent pattern. The router intelligently routes questions to the most appropriate specialist agent based on keywords and patterns.

### 🌟 Language Support

| Language | Status | Production Ready | Package Support |
|----------|--------|------------------|-----------------|
| **JavaScript** | ✅ Stable | ✅ Yes | ✅ Full npm ecosystem |
| **Python** | ✅ Beta | ⚠️ Standard library only | ⚠️ Dev-only (FastAPI, etc.) |

## 🏗️ Architecture

### Core Components

1. **BaseAgent** - Foundation class providing common functionality (CORS, caching, AI calls, MCP server)
2. **RouterAgent** - Specialized router that uses ToolRegistry to route questions to specialist agents  
3. **ToolRegistry** - Dynamic tool discovery and routing system with scoring
4. **AgentBuilder** - Generates complete agent packages from JSON configuration

### Agent Types

- **Router Agent**: Routes questions to specialized agents, falls back to local AI
- **Specialist Agent**: Focused on specific domains (e.g., vulnerabilities, threat intelligence)

## 🚀 Quick Start

### Choose Your Language

#### 🟨 JavaScript (Recommended for Production)
```bash
cd generators/javascript
node build-agent.js configs/cybersec-router.json ../../cybersec-js
```

#### 🐍 Python (Great for Development)
```bash
cd generators/python  
python3 agent_builder.py configs/cybersec-router.json ../../cybersec-py
```

### Deploy Your Agent
```bash
cd your-agent-directory
export CLOUDFLARE_API_TOKEN="your-token-here"
./scripts/deploy.sh
```

## 📁 Project Structure

```
agent-framework/
├── README.md                    # This file
├── generators/                  # Language-specific generators
│   ├── javascript/             # JavaScript/Node.js generator
│   │   ├── agent-builder.js    # JS agent builder
│   │   ├── base-agent.js       # JS base agent class
│   │   ├── router-agent.js     # JS router implementation
│   │   ├── tool-registry.js    # JS routing logic
│   │   ├── config-schema.js    # Configuration validation
│   │   ├── build-agent.js      # CLI build tool
│   │   └── configs/            # Example JS configurations
│   └── python/                 # Python generator  
│       ├── agent_builder.py    # Python agent builder
│       ├── agent_framework/    # Python framework modules
│       │   ├── __init__.py
│       │   ├── base_agent.py   # Python base agent class
│       │   ├── router_agent.py # Python router implementation
│       │   └── tool_registry.py # Python routing logic
│       └── configs/            # Example Python configurations
└── docs/                       # Documentation
```

## 🔧 Language Comparison

### JavaScript Implementation
✅ **Advantages:**
- Full npm package ecosystem in production
- Mature Cloudflare Workers support
- Rich web framework options (Express, Hono, etc.)
- Extensive third-party integrations

⚠️ **Considerations:**
- Slightly larger bundle sizes
- Callback/Promise complexity for some use cases

### Python Implementation  
✅ **Advantages:**
- Clean, readable syntax with type hints
- Standard library rich for many use cases
- Native async/await support
- Familiar to data science/ML teams
- FFI access to all JavaScript APIs

⚠️ **Limitations:**
- Beta status on Cloudflare Workers
- Third-party packages work in dev only (not production)
- Must use standard library for production deployments

## 📚 Configuration Schema

Both languages use the same JSON configuration format:

### Router Agent Configuration
```json
{
  "type": "router",
  "name": "AI Router",
  "description": "Routes questions to specialized agents",
  "systemPrompt": "You are an AI assistant that routes questions...",
  "domain": "router.example.com",
  "accountId": "your-account-id",
  "zoneId": "your-zone-id",
  "registry": {
    "tools": [
      {
        "id": "specialist1",
        "name": "Specialist Name",
        "description": "What this specialist does",
        "endpoint": "https://specialist.domain.com",
        "mcpTool": "tool_name",
        "keywords": ["keyword1", "keyword2"],
        "patterns": ["regex1", "regex2"],
        "priority": 10
      }
    ]
  }
}
```

### Specialist Agent Configuration
```json
{
  "type": "specialist",
  "name": "Domain Expert",
  "description": "Specialized in specific domain",
  "systemPrompt": "You are a specialist in...",
  "domain": "specialist.example.com",
  "accountId": "your-account-id", 
  "zoneId": "your-zone-id",
  "mcpToolName": "specialist_tool",
  "expertise": "domain expertise",
  "keywords": ["domain", "specific", "terms"],
  "patterns": ["domain-specific regex"],
  "priority": 5
}
```

## 🎯 Use Case Recommendations

### Choose JavaScript When:
- Building production applications with complex dependencies
- Need extensive third-party integrations
- Working with existing JavaScript/Node.js ecosystems
- Require mature package ecosystem support

### Choose Python When:
- Team prefers Python syntax and paradigms
- Building AI/ML-focused agents
- Prototyping and development work
- Standard library meets your needs
- Want type safety with modern Python features

## 🚀 Advanced Features

### Dynamic Tool Registry
Agents can register themselves dynamically:

```bash
# JavaScript
POST /admin/tools
{
  "tool": {
    "id": "new-specialist",
    "name": "New Specialist", 
    "endpoint": "https://new.domain.com",
    "keywords": ["specialized", "terms"]
  }
}
```

```python
# Python (same API)
import json
from js import fetch

tool_data = {
    "tool": {
        "id": "new-specialist",
        "name": "New Specialist",
        "endpoint": "https://new.domain.com", 
        "keywords": ["specialized", "terms"]
    }
}
```

### MCP Server Interface
All agents automatically expose MCP endpoints:
- `POST /mcp` - MCP protocol endpoint
- Tools list: `{"method": "tools/list"}`
- Tool calls: `{"method": "tools/call", "params": {...}}`

### Performance Optimizations

#### JavaScript
- ES modules with tree shaking
- Efficient V8 execution
- npm package bundling

#### Python  
- Pyodide snapshot at deploy time
- FFI for JavaScript API access
- Standard library optimization

## 📊 Code Reduction Benefits

### Before Framework
- **Per Agent**: ~400 lines of duplicated code
- **Total for 3 agents**: ~1200 lines with significant duplication

### After Framework
- **JavaScript agents**: ~70 lines of configuration (95% reduction)
- **Python agents**: ~65 lines of configuration (96% reduction)
- **Framework**: ~2000 lines total (reusable across all agents)

### 🎉 Key Benefits
✅ **95%+ code reduction** per new agent  
✅ **Consistent behavior** across all agents  
✅ **Zero duplication** of common functionality  
✅ **Multi-language support** for team preferences  
✅ **Template-based generation** for rapid development  
✅ **Centralized updates** through framework  

## 🛠️ Development Workflow

### 1. Choose Your Language
```bash
# JavaScript
cd generators/javascript

# Python  
cd generators/python
```

### 2. Create Configuration
```bash
# Copy and modify example
cp configs/judge-specialist.json configs/my-specialist.json
# Edit configuration for your domain
```

### 3. Generate Agent
```bash
# JavaScript
node build-agent.js configs/my-specialist.json ../my-agent

# Python
python3 agent_builder.py configs/my-specialist.json ../my-agent
```

### 4. Deploy Agent
```bash
cd ../my-agent
export CLOUDFLARE_API_TOKEN="your-token"
./scripts/deploy.sh
```

### 5. Register with Router
Add the new specialist to your router's registry configuration and redeploy.

## 🐛 Troubleshooting

### Common Issues

**JavaScript Import Errors**
- Check ES module syntax
- Verify file paths are correct
- Ensure dependencies are installed

**Python Import Errors**  
- Ensure `agent_framework` directory is present
- Check Python syntax compatibility
- Verify FFI imports are correct for Workers environment

**Deployment Failures**
- Confirm API token permissions
- Check account and zone IDs
- Verify domain DNS configuration
- For Python: ensure `python_workers` compatibility flag is set

**Routing Not Working**
- Check keyword case sensitivity  
- Test regex patterns with actual questions
- Verify MCP endpoint accessibility
- Ensure tool registry is properly configured

## 🔮 Future Roadmap

### JavaScript
- [ ] Hono framework integration
- [ ] Advanced middleware support
- [ ] WebAssembly module support
- [ ] Edge-side rendering optimizations

### Python
- [ ] Production package support (when available)
- [ ] FastAPI integration for production
- [ ] Advanced typing and validation
- [ ] NumPy/Scientific computing support

### Framework
- [ ] Rust generator
- [ ] Go generator  
- [ ] Visual agent builder UI
- [ ] Metrics and monitoring dashboard
- [ ] Auto-scaling based on load

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Choose your language implementation
4. Add tests for new functionality
5. Update documentation
6. Submit pull request

### Language-Specific Guidelines

**JavaScript**
- Use ES2022+ features
- Follow ESLint configuration
- Add JSDoc comments
- Write Jest tests

**Python**
- Use Python 3.9+ features  
- Follow Black formatting
- Add type hints
- Write pytest tests

## 📄 License

MIT License - see LICENSE file for details

---

## 🎯 Examples

### Quick Start Examples

#### JavaScript Specialist Agent
```bash
cd generators/javascript
node build-agent.js configs/judge-specialist.json ../../judge-js
cd ../../judge-js
./scripts/deploy.sh
```

#### Python Router Agent
```bash
cd generators/python
python3 agent_builder.py configs/cybersec-router.json ../../cybersec-py
cd ../../cybersec-py
./scripts/deploy.sh
```

#### Mixed Language Deployment
```bash
# Deploy Python specialist
cd generators/python
python3 agent_builder.py configs/judge-specialist.json ../../judge-py

# Deploy JavaScript router that uses Python specialist
cd ../javascript  
node build-agent.js configs/cybersec-router.json ../../cybersec-js
# Edit cybersec-js config to point to judge-py endpoint

# Deploy both
cd ../../judge-py && ./scripts/deploy.sh
cd ../cybersec-js && ./scripts/deploy.sh
```

**The beauty of this framework**: Language choice is per-agent. You can have Python specialists and JavaScript routers, or any combination that fits your team's expertise and requirements!

---

*Multi-Language Agent Framework v2.0*  
**Powered by:** [Cloudflare Workers](https://workers.cloudflare.com/) | [Workers AI](https://ai.cloudflare.com/) | JavaScript & Python 🚀