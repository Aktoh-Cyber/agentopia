# Cookiecutter JavaScript Specialist Agent

A cookiecutter template for creating specialized AI agents on Cloudflare Workers. Specialist agents focus on specific domains and can be integrated with router agents for intelligent question routing.

## Features

- 🎯 **Domain Specialization**: Focused expertise in specific areas
- 🔧 **MCP Protocol Support**: Exposes Model Context Protocol endpoints
- 🚀 **Cloudflare Workers**: Serverless deployment with global edge network
- 💾 **Response Caching**: Built-in caching for improved performance
- 🤖 **AI Integration**: Uses Cloudflare Workers AI models
- 🔍 **Pattern Matching**: Keywords and regex patterns for specialization

## Quick Start

### Prerequisites

- Python 3.7+ with cookiecutter installed
- Node.js 16+ and npm
- Cloudflare account with Workers enabled
- Wrangler CLI installed (`npm install -g wrangler`)

### Generate Your Agent

```bash
# Install cookiecutter if not already installed
pip install cookiecutter

# Generate from this template
cookiecutter https://github.com/Aktoh-Cyber/cc-js-specialist-agent

# Or from local directory
cookiecutter path/to/cc-js-specialist-agent
```

### Configuration Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `project_name` | Name of your specialist agent | Domain Specialist Agent |
| `description` | Agent description | A specialized AI agent... |
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
your-specialist-agent/
├── src/
│   └── index.js           # Main agent implementation
├── agent-framework/       # Agent framework code
│   ├── base-agent.js
│   └── tool-registry.js
├── scripts/
│   └── deploy.sh         # Deployment script
├── .github/
│   └── workflows/
│       └── deploy.yml    # GitHub Actions CI/CD
├── wrangler.toml         # Cloudflare Workers config
├── package.json          # Node.js dependencies
├── README.md            # Project documentation
├── .env.local.example   # Environment variables template
└── .gitignore
```

## Development

### Local Development

```bash
# Navigate to your generated agent
cd your-specialist-agent

# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local with your Cloudflare credentials

# Run locally
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

Edit `src/index.js` and update the `systemPrompt` in the configuration:

```javascript
systemPrompt: `Your custom prompt here...`
```

### Adding Custom Logic

Extend the `processQuestion` method in `src/index.js`:

```javascript
async processQuestion(env, question) {
  // Add your custom logic here
  const customProcessing = await this.myCustomMethod(question);
  
  // Continue with standard processing
  return super.processQuestion(env, question);
}
```

### Adjusting Keywords and Patterns

Update the `keywords` and `patterns` arrays in your configuration to better match your domain:

```javascript
keywords: ["specific", "domain", "terms"],
patterns: ["domain-specific.*regex", "another.*pattern"]
```

## Advanced Features

### Response Caching

Responses are cached by default for 1 hour (3600 seconds). Adjust in configuration:

```javascript
cacheEnabled: true,
cacheTTL: 7200  // 2 hours
```

### Custom AI Models

Change the AI model in configuration:

```javascript
model: '@cf/meta/llama-3.1-8b-instruct'  // Smaller, faster model
```

### Environment Variables

Use environment variables for sensitive data:

```javascript
cloudflareAccountId: env.CLOUDFLARE_ACCOUNT_ID || ''
```

## Troubleshooting

### Common Issues

1. **Deployment Fails**
   - Check Cloudflare API token permissions
   - Verify account and zone IDs
   - Ensure domain DNS is configured

2. **Agent Not Responding**
   - Check wrangler logs: `npx wrangler tail`
   - Verify AI model is available in your region
   - Check cache settings

3. **MCP Integration Issues**
   - Ensure endpoint URL is correct
   - Verify CORS headers are properly set
   - Check tool name matches configuration

## Contributing

This template is part of the Agentopia framework. Contributions welcome!

1. Fork the repository
2. Create your feature branch
3. Test your changes
4. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

- [Documentation](https://github.com/Aktoh-Cyber/cc-js-specialist-agent)
- [Issues](https://github.com/Aktoh-Cyber/cc-js-specialist-agent/issues)
- [Agentopia Framework](https://github.com/yourusername/agentopia)

---

Created with ❤️ for the Cloudflare Workers community