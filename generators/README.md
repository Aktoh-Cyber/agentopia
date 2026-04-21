# Generators Directory

Template-based agent code generators for JavaScript and Python.

## Purpose

Generates complete, deployable Cloudflare Workers agents from JSON configuration files. Reduces agent development from ~400 lines of boilerplate to ~70 lines of JSON config (95% reduction).

## Structure

| Directory | Description |
|-----------|-------------|
| `javascript/` | JS agent generator with LangChain.js integration |
| `python/` | Python agent generator with Pyodide-compatible output |

## JavaScript Generator

- `agent-builder.js` - Main builder: reads JSON config, generates agent source, wrangler.toml, deploy script
- `base-agent.js` - BaseAgent template with LangChain.js, CORS, caching, MCP
- `router-agent.js` - RouterAgent template with ToolRegistry-based routing
- `tool-registry.js` - Dynamic routing with keyword/regex scoring
- `langgraph-agent.js` - LangGraph multi-agent pattern support
- `evolve-bridge.js` - Bridge for Evolve dynamic tool generation
- `config-schema.js` - Configuration validation
- `configs/` - Pre-built agent configurations (judge, scout, lancer, shield, infosec-supervisor)

## Python Generator

- `agent_builder.py` - `PythonAgentBuilder` class: validates config, generates Pyodide-compatible agents
- `agent_framework/` - Python BaseAgent, RouterAgent, ToolRegistry (standard library only for Pyodide compatibility)
- `templates/` - Output templates for generated agents
- `configs/` - Agent configuration files

## Usage

```bash
# JavaScript
cd generators/javascript
node build-agent.js configs/infosec-supervisor.json ../../output-dir

# Python
cd generators/python
python3 agent_builder.py configs/infosec-supervisor.json ../../output-dir
```

## Configuration Schema

Both languages use identical JSON configs with fields: `name`, `description`, `systemPrompt`, `domain`, `accountId`, `zoneId`, `model`, `maxTokens`, `temperature`, `keywords[]`, `patterns[]`, `registry.tools[]`.
