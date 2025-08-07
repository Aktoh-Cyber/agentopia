# Cookiecutter Python Router Agent

A cookiecutter template for creating Python-based AI router agents on Cloudflare Workers. Router agents intelligently route questions to specialized agents based on keywords and patterns.

## Features

- 🔀 **Intelligent Routing**: Routes questions to the most appropriate specialist
- 🐍 **Python on Workers**: Uses Pyodide runtime for Python in Cloudflare Workers
- 🔧 **MCP Protocol Support**: Exposes Model Context Protocol endpoints
- 🚀 **Cloudflare Workers**: Serverless deployment with global edge network
- 💾 **Response Caching**: Built-in caching for improved performance
- 🤖 **AI Integration**: Uses Cloudflare Workers AI models
- 📊 **Dynamic Registry**: Add/remove specialists at runtime

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
cookiecutter https://github.com/Aktoh-Cyber/cc-py-router-agent

# Or from local directory
cookiecutter path/to/cc-py-router-agent
```

### Configuration Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `project_name` | Name of your router agent | Python AI Router |
| `description` | Agent description | A Python-based AI router... |
| `domain` | Your Cloudflare domain | router.example.com |
| `cloudflare_account_id` | Cloudflare account ID | (optional) |
| `cloudflare_zone_id` | Cloudflare zone ID | (optional) |
| `ai_model` | AI model to use | @cf/meta/llama-3.1-70b-instruct |
| `registry_json` | Initial tool registry (JSON) | {"tools": []} |
| `system_prompt` | AI system prompt | You are an intelligent router... |

## Project Structure

After generation, your project will have:

```
your-python-router/
├── src/
│   └── entry.py           # Main Python agent implementation
├── agent_framework/       # Python agent framework
│   ├── __init__.py
│   ├── base_agent.py
│   ├── router_agent.py
│   └── tool_registry.py
├── scripts/
│   └── deploy.sh         # Deployment script
├── .github/
│   └── workflows/
│       └── deploy.yml    # GitHub Actions CI/CD
├── wrangler.toml         # Cloudflare Workers config
├── pyproject.toml        # Python dependencies
├── README.md            # Project documentation
├── .env.local.example   # Environment variables template
└── .gitignore
```

## Python on Cloudflare Workers

This template uses Pyodide to run Python on Cloudflare Workers. Important notes:

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
cd your-python-router

# Install Python dependencies (development)
pip install -r requirements-dev.txt

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
  -d '{"question": "Route this to a specialist"}'

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

## Adding Specialist Agents

### Static Configuration

Add specialists to the `registry_json` in your configuration:

```json
{
  "tools": [
    {
      "id": "security-specialist",
      "name": "Security Expert",
      "description": "Handles security questions",
      "endpoint": "https://security.domain.com",
      "keywords": ["security", "vulnerability", "owasp"],
      "patterns": [".*CVE-.*", ".*security.*"],
      "priority": 10
    }
  ]
}
```

### Dynamic Registration

Register specialists at runtime via the admin endpoint:

```bash
curl -X POST http://your-router.domain.com/admin/tools \
  -H "Content-Type: application/json" \
  -d '{
    "tool": {
      "id": "new-specialist",
      "name": "New Specialist",
      "endpoint": "https://new.domain.com",
      "keywords": ["specific", "terms"],
      "priority": 5
    }
  }'
```

## Python-Specific Features

### FFI JavaScript Integration

```python
from js import fetch, console, JSON

# Call JavaScript APIs
response = await fetch(url)
data = await response.json()
console.log("Data:", data)
```

### Type Hints

```python
from typing import Dict, List, Optional

async def process_question(
    self, 
    env: Any, 
    question: str
) -> Dict[str, Any]:
    """Process and route questions with type safety."""
    pass
```

### Async/Await

```python
async def fetch_from_specialist(self, url: str) -> Dict:
    """Asynchronously fetch from specialist."""
    response = await fetch(url)
    return await response.json()
```

## Routing Logic

The router uses a scoring system:

1. **Keyword Matching**: +1 point per keyword match
2. **Pattern Matching**: +2 points per regex match
3. **Priority Multiplier**: Final score × priority
4. **Fallback**: Local AI if no specialist matches

## Customization

### Modifying the System Prompt

Edit `src/entry.py` and update the `system_prompt`:

```python
system_prompt = """Your custom routing logic here..."""
```

### Adding Custom Routing Logic

Extend the `RouterAgent` class:

```python
class CustomRouter(RouterAgent):
    async def custom_routing(self, question: str) -> Optional[str]:
        # Add custom logic
        if "emergency" in question.lower():
            return "https://emergency.specialist.com"
        return None
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

3. **Routing Not Working**
   - Check specialist endpoints are accessible
   - Verify keywords and patterns
   - Review scoring logic in logs

4. **Performance Issues**
   - Enable caching
   - Optimize regex patterns
   - Consider reducing specialist timeout

## Python vs JavaScript

### When to Use Python Router
- Team expertise in Python
- Need for specific Python libraries (development)
- Prefer Python's syntax and paradigms
- Integration with Python-based systems

### When to Use JavaScript Router
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

- [Documentation](https://github.com/Aktoh-Cyber/cc-py-router-agent)
- [Issues](https://github.com/Aktoh-Cyber/cc-py-router-agent/issues)
- [Agentopia Framework](https://github.com/yourusername/agentopia)

---

Created with ❤️ for the Python and Cloudflare Workers community