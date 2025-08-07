# {{cookiecutter.project_name}}

{{cookiecutter.description}}

## Overview

This is a specialized AI agent focused on **{{cookiecutter.expertise}}**. It uses keyword matching and pattern recognition to identify relevant questions and provide expert-level responses.

## Features

- 🎯 **Specialized Expertise**: Focused on {{cookiecutter.expertise}}
- 🤖 **AI-Powered**: Uses {{cookiecutter.ai_model}} for intelligent responses
- 💾 **Response Caching**: Caches responses for {{cookiecutter.cache_ttl}} seconds
- 🔧 **MCP Protocol**: Exposes tool endpoints for integration with router agents
- 🚀 **Edge Deployment**: Runs on Cloudflare Workers global network

## Quick Start

### Prerequisites

- Node.js 16+ and npm
- Cloudflare account with Workers enabled
- Wrangler CLI (`npm install -g wrangler`)

### Installation

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.local.example .env.local
# Edit .env.local with your Cloudflare credentials
```

### Local Development

```bash
# Run locally
npx wrangler dev

# Test the agent
curl -X POST http://localhost:8787 \
  -H "Content-Type: application/json" \
  -d '{"question": "{{cookiecutter.examples_json[0]}}"}'
```

## Configuration

### Specialization Settings

This agent is configured to respond to:

**Keywords**: {{cookiecutter.keywords_json}}

**Patterns**: {{cookiecutter.patterns_json}}

**Priority**: {{cookiecutter.priority}} (used for routing decisions)

### AI Configuration

- **Model**: {{cookiecutter.ai_model}}
- **Max Tokens**: {{cookiecutter.max_tokens}}
- **Temperature**: {{cookiecutter.temperature}}

## Deployment

### Manual Deployment

```bash
# Set your Cloudflare API token
export CLOUDFLARE_API_TOKEN="your-token-here"

# Deploy to production
./scripts/deploy.sh
```

### GitHub Actions

This project includes GitHub Actions for automated deployment:

1. Add `CLOUDFLARE_API_TOKEN` to your GitHub repository secrets
2. Push to main branch to trigger deployment

## MCP Integration

This specialist agent exposes MCP endpoints for integration with router agents:

### Available Endpoints

- `POST /mcp` - Main MCP protocol endpoint

### Tool Definition

```json
{
  "name": "{{cookiecutter.mcp_tool_name}}",
  "description": "{{cookiecutter.description}}",
  "expertise": "{{cookiecutter.expertise}}",
  "keywords": {{cookiecutter.keywords_json}},
  "patterns": {{cookiecutter.patterns_json}},
  "priority": {{cookiecutter.priority}}
}
```

### Integration Example

To integrate with a router agent, add this configuration:

```json
{
  "id": "{{cookiecutter.project_slug}}",
  "name": "{{cookiecutter.project_name}}",
  "description": "{{cookiecutter.description}}",
  "endpoint": "https://{{cookiecutter.domain}}",
  "mcpTool": "{{cookiecutter.mcp_tool_name}}",
  "keywords": {{cookiecutter.keywords_json}},
  "patterns": {{cookiecutter.patterns_json}},
  "priority": {{cookiecutter.priority}}
}
```

## API Reference

### Main Endpoint

`POST /`

Request:
```json
{
  "question": "Your question here"
}
```

Response:
```json
{
  "answer": "The specialist's response",
  "cached": false,
  "relevant": true,
  "source": "{{cookiecutter.project_name}}"
}
```

### MCP Endpoint

`POST /mcp`

List tools:
```json
{
  "method": "tools/list"
}
```

Call tool:
```json
{
  "method": "tools/call",
  "params": {
    "name": "{{cookiecutter.mcp_tool_name}}",
    "arguments": {
      "question": "Your question"
    }
  }
}
```

## Customization

### Modifying Expertise

Edit `src/index.js` to adjust the specialization:

1. Update `keywords` array for simple matching
2. Modify `patterns` array for regex matching
3. Adjust `systemPrompt` for different expertise

### Adding Custom Logic

Extend the `processQuestion` method:

```javascript
async processQuestion(env, question) {
  // Add custom preprocessing
  const processed = await this.customLogic(question);
  
  // Continue with standard processing
  return super.processQuestion(env, processed);
}
```

## Examples

### Sample Questions

The agent is configured to handle questions like:
- Example questions from your configuration will appear here

## Monitoring

View logs and metrics:

```bash
# View real-time logs
npx wrangler tail

# View deployment status
npx wrangler deployments list
```

## Troubleshooting

### Common Issues

1. **Agent not responding to questions**
   - Check if keywords/patterns match the question
   - Verify the relevance check in logs
   - Test with exact keyword matches first

2. **MCP integration not working**
   - Ensure endpoint URL is correct
   - Check CORS headers in response
   - Verify tool name matches configuration

3. **Deployment failures**
   - Verify Cloudflare API token permissions
   - Check wrangler.toml configuration
   - Ensure domain is properly configured

## Support

- **Author**: {{cookiecutter.author_name}}
- **Email**: {{cookiecutter.author_email}}
- **Domain**: https://{{cookiecutter.domain}}

## License

MIT License - see LICENSE file for details

---

Generated with [Cookiecutter JavaScript Specialist Agent Template](https://github.com/Aktoh-Cyber/cc-js-specialist-agent)