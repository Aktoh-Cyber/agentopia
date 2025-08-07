# Cookiecutter Python Specialist Agent

A cookiecutter template for creating Python-based specialized AI agents on Cloudflare Workers. Specialist agents focus on specific domains and can be integrated with router agents for intelligent question routing.

## Features

- 🎯 **Domain Specialization**: Focused expertise in specific areas
- 🐍 **Python on Workers**: Uses Pyodide runtime for Python execution
- 🔧 **MCP Protocol Support**: Exposes Model Context Protocol endpoints
- 🚀 **Cloudflare Workers**: Serverless deployment with global edge network
- 💾 **Response Caching**: Built-in caching for improved performance
- 🤖 **AI Integration**: Uses Cloudflare Workers AI models
- 🔍 **Pattern Matching**: Keywords and regex patterns for specialization

## Quick Start

### Prerequisites

- Python 3.7+ with cookiecutter installed
- Node.js 16+ and npm (for Wrangler CLI)
- Cloudflare account with Workers enabled
- Wrangler CLI installed (`npm install -g wrangler`)

### Generate Your Agent

```bash
# Install cookiecutter if not already installed
pip install cookiecutter

# Generate from this template
cookiecutter https://github.com/Aktoh-Cyber/cc-py-specialist-agent

# Or from local directory
cookiecutter path/to/cc-py-specialist-agent
```

### Configuration Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `project_name` | Name of your specialist agent | Python Domain Specialist |
| `description` | Agent description | A Python-based specialized... |
| `domain` | Your Cloudflare domain | specialist.example.com |
| `cloudflare_account_id` | Cloudflare account ID | (optional) |
| `cloudflare_zone_id` | Cloudflare zone ID | (optional) |
| `ai_model` | AI model to use | @cf/meta/llama-3.1-70b-instruct |
| `mcp_tool_name` | MCP tool identifier | specialist_tool |
| `expertise` | Domain expertise description | Domain expertise description |
| `keywords_json` | Keywords for routing (JSON array) | ["keyword1", "keyword2"] |
| `patterns_json` | Regex patterns (JSON array) | ["pattern1.*regex"] |
| `priority` | Routing priority (1-10) | 5 |
| `system_prompt` | AI system prompt | You are a domain specialist... |

## Project Structure

After generation, your project will have:

```
your-python-specialist/
├── src/
│   └── entry.py           # Main Python agent implementation
├── agent_framework/       # Python agent framework
│   ├── __init__.py
│   ├── base_agent.py
│   └── specialist_agent.py
├── scripts/
│   └── deploy.sh         # Deployment script
├── .github/
│   └── workflows/
│       └── deploy.yml    # GitHub Actions CI/CD
├── wrangler.toml         # Cloudflare Workers config
├── pyproject.toml        # Python project configuration
├── README.md            # Project documentation
├── .env.local.example   # Environment variables template
└── .gitignore
```

## Python on Cloudflare Workers

This template uses Pyodide to run Python on Cloudflare Workers:

### Production Constraints
- **Standard Library Only**: Third-party packages work in development but not production
- **FFI Imports**: Use `from js import fetch, console` for JavaScript APIs
- **Async/Await**: Full async support with Python's native syntax
- **Type Hints**: Encouraged for better code quality

### Development vs Production
- **Development**: Full Python ecosystem available locally
- **Production**: Limited to standard library for reliability
- **Framework Design**: Uses only standard library to ensure production compatibility

## Development

### Local Development

```bash
# Navigate to your generated agent
cd your-python-specialist

# Install Python dependencies (development)
pip install -e .[dev]

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local with your Cloudflare credentials

# Run locally with Wrangler
npx wrangler dev
```

### Testing Your Agent

```bash
# Test the agent endpoint
curl -X POST http://localhost:8787 \
  -H "Content-Type: application/json" \
  -d '{"question": "What is your specialty?"}'

# Test MCP endpoint
curl -X POST http://localhost:8787/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list"}'
```

## Deployment

### Manual Deployment

```bash
# Set your Cloudflare API token
export CLOUDFLARE_API_TOKEN="your-token-here"

# Deploy to Cloudflare Workers
./scripts/deploy.sh
```

### GitHub Actions Deployment

1. Add your Cloudflare API token to GitHub secrets as `CLOUDFLARE_API_TOKEN`
2. Push to your repository
3. GitHub Actions will automatically deploy on push to main branch

## MCP Integration

Specialist agents automatically expose MCP endpoints:

- `POST /mcp` - Main MCP protocol endpoint
- Methods:
  - `tools/list` - List available tools
  - `tools/call` - Call the specialist with a question

### Integration with Router Agents

To integrate with a router agent, add your specialist to the router's registry:

```json
{
  "id": "your-specialist",
  "name": "Your Specialist Name",
  "description": "What your specialist does",
  "endpoint": "https://your-specialist.domain.com",
  "mcpTool": "specialist_tool",
  "keywords": ["keyword1", "keyword2"],
  "patterns": ["pattern.*regex"],
  "priority": 5
}
```

## Customization

### Modifying the System Prompt

Edit `src/entry.py` and update the `system_prompt`:

```python
system_prompt = """Your custom prompt here..."""
```

### Adding Custom Logic

Extend the `process_question` method:

```python
async def process_question(self, env: Any, question: str) -> Dict[str, Any]:
    # Add your custom logic here
    custom_processing = await self.my_custom_method(question)
    
    # Continue with standard processing
    return await super().process_question(env, question)
```

### Adjusting Keywords and Patterns

Update the configuration in your generated project:

```python
keywords = ["specific", "domain", "terms"]
patterns = ["domain-specific.*regex", "another.*pattern"]
```

## Python-Specific Features

### Type Hints

```python
from typing import Dict, List, Optional, Any

async def is_question_relevant(self, question: str) -> bool:
    """Check if question matches our expertise."""
    pass
```

### FFI JavaScript Integration

```python
from js import fetch, console, Response, Headers

# Use JavaScript APIs
console.log("Processing question...")
response = await fetch(url)
```

### Async/Await

```python
async def handle_request(self, request: Any, env: Any) -> Any:
    """Async request handling."""
    result = await self.process_question(env, question)
    return Response.new(json.dumps(result))
```

## Advanced Features

### Response Caching

Responses are cached by default for 1 hour (3600 seconds):

```python
cache_enabled = True
cache_ttl = 7200  # 2 hours
```

### Custom AI Models

Change the AI model in configuration:

```python
ai_model = '@cf/meta/llama-3.1-8b-instruct'  # Smaller, faster model
```

### Environment Variables

Use environment variables for sensitive data:

```python
cloudflare_account_id = env.CLOUDFLARE_ACCOUNT_ID or ''
```

## Troubleshooting

### Common Issues

1. **Python Import Errors**
   - Ensure using standard library only for production
   - Check FFI imports are correct
   - Verify Pyodide compatibility

2. **Deployment Fails**
   - Check `compatibility_flags = ["python_workers"]` in wrangler.toml
   - Verify API token permissions
   - Ensure Python syntax is compatible

3. **Agent Not Responding**
   - Check wrangler logs: `npx wrangler tail`
   - Verify AI model is available
   - Check cache settings

4. **MCP Integration Issues**
   - Ensure endpoint URL is correct
   - Verify CORS headers are set
   - Check tool name matches configuration

## Python vs JavaScript

### When to Use Python Specialist
- Team expertise in Python
- Prefer Python's syntax and paradigms
- Development work with full ecosystem
- Standard library meets production needs

### When to Use JavaScript Specialist
- Need third-party packages in production
- Slightly better performance
- More mature Workers ecosystem
- Broader package availability

## Contributing

This template is part of the Agentopia framework. Contributions welcome!

1. Fork the repository
2. Create your feature branch
3. Test your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- [Documentation](https://github.com/Aktoh-Cyber/cc-py-specialist-agent)
- [Issues](https://github.com/Aktoh-Cyber/cc-py-specialist-agent/issues)
- [Agentopia Framework](https://github.com/yourusername/agentopia)

---

Created with ❤️ for the Python and Cloudflare Workers community