# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Architecture

This is a multi-language agent framework for building AI agents on Cloudflare Workers with intelligent routing and MCP (Model Context Protocol) support. The framework uses a router-agent pattern where specialist agents handle domain-specific questions and routers intelligently route requests.

### Core Architecture

- **BaseAgent**: Foundation class providing CORS, caching, AI calls, and MCP server functionality
- **RouterAgent**: Routes questions to specialist agents using ToolRegistry scoring
- **ToolRegistry**: Dynamic routing system with keyword/regex pattern matching and priority scoring
- **AgentBuilder**: Template-based code generation from JSON configuration

### Multi-Language Structure

The framework supports parallel JavaScript and Python implementations:

```
generators/
├── javascript/          # Production-ready, full npm ecosystem
│   ├── base-agent.js
│   ├── router-agent.js
│   ├── tool-registry.js
│   └── agent-builder.js
└── python/             # Beta, standard library only in production
    ├── agent_framework/
    │   ├── base_agent.py
    │   ├── router_agent.py
    │   └── tool_registry.py
    └── agent_builder.py
```

**Key Constraint**: Python production deployments use Pyodide runtime. Third-party packages are supported via Pywrangler bundling, but must be WebAssembly-compatible. For maximum compatibility, this framework uses standard library only.

## Common Development Commands

### Agent Generation
```bash
# JavaScript agent
cd generators/javascript
node build-agent.js configs/infosec-router.json ../../output-dir

# Python agent  
cd generators/python
python3 agent_builder.py configs/infosec-router.json ../../output-dir

# LangGraph pattern agents (both languages)
node build-agent.js configs/supervisor-example.json ../../supervisor-demo
python3 agent_builder.py configs/committee-example.json ../../committee-demo
```

### Development and Deployment
```bash
# Local development (in generated agent directory)
npx wrangler dev

# Deploy agent
export CLOUDFLARE_API_TOKEN="your-token"
./scripts/deploy.sh

# Python code formatting (development)
python -m black src/
python -m mypy src/
```

### Framework Development
```bash
# Test agent generation
cd generators/javascript && node build-agent.js configs/judge-specialist.json ../test-output
cd generators/python && python3 agent_builder.py configs/judge-specialist.json ../test-output

# Validate configuration schemas
node config-schema.js validate configs/example.json  # JavaScript only
```

## Configuration Architecture

Both languages use identical JSON configuration schemas:

### Agent Types
- **Router**: Contains `registry.tools[]` array with specialist agent endpoints, keywords, patterns
- **Specialist**: Contains `mcpToolName`, `keywords[]`, `patterns[]`, and domain `expertise`

### Key Configuration Fields
- `systemPrompt`: AI behavior definition
- `domain`: Cloudflare Workers custom domain
- `accountId`/`zoneId`: Cloudflare deployment targets
- `registry.tools[]`: Routing configuration for specialist agents
- `keywords[]`: Simple string matching for routing
- `patterns[]`: Regex patterns for advanced routing

## Routing Logic

The ToolRegistry implements score-based routing:
- Keywords: +1 point each
- Regex patterns: +2 points each  
- Priority multiplier applied to final score
- Highest scoring specialist handles the request
- Falls back to local AI if no specialist matches

## MCP Protocol Integration

All agents automatically expose MCP endpoints:
- `POST /mcp` - MCP protocol endpoint
- `tools/list` method for capability discovery
- `tools/call` method for agent invocation
- `POST /admin/tools` for dynamic tool registration

## Deep Agent Patterns

For advanced multi-agent architectures and cognitive patterns, see [DEEP_AGENT_PATTERNS.md](./DEEP_AGENT_PATTERNS.md). This document covers 24 different architectural patterns including:

- **Multi-Agent Patterns**: Network, Supervisor, Hierarchical, Router, Tool-Calling
- **Cognitive Architectures**: Single LLM, Chain of LLM Calls, State Machine, Autonomous Agent
- **Ensemble Patterns**: Committee, Consultant, Voting-Based Aggregator
- **Advanced Patterns**: Swarm, Auction-Based, Pub-Sub, Reflection

Each pattern includes Mermaid diagrams and use case guidance for building sophisticated agent systems with LangGraph.

## Language-Specific Development Notes

### JavaScript Implementation
- Uses ES modules with tree shaking
- Full npm ecosystem available in production
- Mature Cloudflare Workers support
- No import restrictions
- **LangChain.js integration**: Full LangChain.js support with custom Cloudflare Workers LLM

### Python Implementation  
- Uses FFI imports for JavaScript API access: `from js import console, fetch`
- **Package support**: Third-party packages supported via Pywrangler (must be WebAssembly-compatible)
- **Framework design**: Uses standard library only for maximum compatibility and performance
- Type hints and async/await throughout
- Pyodide-based execution environment
- **LangChain-style interface**: Provides familiar LangChain abstractions using only standard library

## Template Generation Architecture

Both implementations use direct file templating rather than complex template engines:

### Generated Files
- `src/entry.py` or `src/index.js`: Main agent logic
- `wrangler.toml`: Cloudflare Workers configuration  
- `scripts/deploy.sh`: Deployment automation
- `README.md`: Agent-specific documentation

### Template Context Variables
- Agent metadata: `name`, `description`, `type`
- Cloudflare config: `domain`, `accountId`, `zoneId`
- AI settings: `model`, `maxTokens`, `temperature`
- Routing config: `keywords_json`, `patterns_json`, `registry_json`

## Performance and Caching

- Response caching with configurable TTL (default 3600s)
- Cold start optimization for both JavaScript and Python
- Python uses Pyodide snapshots for faster execution
- KV namespace binding for distributed caching

## Python LangChain-Style Interface

The Python implementation provides a familiar LangChain-style API while respecting Cloudflare Workers' standard library constraints:

### Available Components
- **Message Types**: `SystemMessage`, `HumanMessage`, `AIMessage`
- **Prompt Templates**: `PromptTemplate`, `ChatPromptTemplate`
- **Chains**: `LLMChain`, `SimpleSequentialChain`, custom `RouterChain`
- **Memory**: `ConversationBufferMemory` for conversation history
- **Output Parsers**: `StrOutputParser`, `JsonOutputParser`
- **LLM Interface**: `CloudflareWorkersLLM` wrapping Cloudflare AI

### Usage Example
```python
# Agents automatically use LangChain-style by default
agent = BaseAgent(config)

# Or explicitly control:
config["useLangchain"] = True  # Enable (default)
config["useLangchain"] = False  # Use legacy interface

# Custom chains and prompts work naturally
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant"),
    ("human", "{question}")
])
```

### Benefits
- Familiar API for LangChain developers
- Smooth migration path for existing code patterns
- Type-safe abstractions
- Zero external dependencies (production-ready)
- Automatic fallback to legacy mode if imports fail

## JavaScript LangChain.js Integration

The JavaScript implementation provides full LangChain.js support with custom integrations for Cloudflare Workers:

### Available Components
- **Full LangChain.js ecosystem**: All standard LangChain.js packages and components
- **Custom CloudflareWorkersLLM**: Native integration with Cloudflare Workers AI
- **Chains**: LLMChain, custom RouterChain, and all standard chains
- **Memory**: BufferMemory and other memory types for conversation tracking
- **Prompts**: ChatPromptTemplate, PromptTemplate with full templating
- **Message Types**: SystemMessage, HumanMessage, AIMessage

### Usage Example
```javascript
import { BaseAgent } from './base-agent.js';

// Agents use LangChain.js by default
const agent = new BaseAgent(config);

// Or explicitly control:
config.useLangchain = true;  // Enable (default)
config.useLangchain = false; // Use legacy interface

// Custom chains work naturally
const prompt = ChatPromptTemplate.fromTemplate("You are {role}. {question}");
const chain = new LLMChain({ llm: agent.llm, prompt });
```

### Router Enhancement
- **RouterChain**: AI-powered routing decisions with confidence scoring
- **Enhanced prompts**: Dynamic routing analysis with JSON responses
- **Fallback support**: Graceful degradation to keyword/pattern matching
- **Visual indicators**: UI shows LangChain.js enhancement status

### Dependencies
```json
{
  "dependencies": {
    "langchain": "^0.1.30",
    "@langchain/core": "^0.1.52", 
    "@langchain/community": "^0.0.45"
  }
}
```

## Code Reduction Benefits

This framework reduces agent development from ~400 lines of boilerplate to ~70 lines of JSON configuration (95% reduction). The template-based approach eliminates duplication while maintaining consistency across all generated agents.