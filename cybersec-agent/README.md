# Cybersecurity AI Assistant

A Cloudflare Worker-powered AI assistant specialized in cybersecurity topics, using Llama 3.1 8B for fast and accurate responses.

🔗 **Live Demo**: https://cybersec.mindhive.tech

## Features

- 🤖 AI-powered Q&A using Cloudflare Workers AI (Llama 3.1 8B)
- 🛡️ Specialized in cybersecurity topics
- ⚖️ **Integrated with Judge**: Automatically defers vulnerability and compliance questions to our specialized Judge service
- ⚡ Fast responses with optional KV caching
- 🎨 Clean, professional web interface
- 🔌 RESTful API endpoint
- 🔄 MCP Client integration for agent-to-agent communication

## Project Structure

```
cybersec-agent/
├── src/
│   ├── index.js              # Main worker code with Judge integration
│   ├── mcp-client.js         # MCP client for communicating with Judge
│   └── index-no-kv.js.backup # Fallback version without caching
├── scripts/                  # Deployment and setup scripts
│   ├── deploy-all.sh         # Full deployment with KV
│   ├── deploy-no-kv.sh       # Deployment without KV
│   ├── create-dns.sh         # DNS record creation
│   └── create-route.sh       # Worker route creation
├── package.json
├── wrangler.toml            # Cloudflare Worker configuration
└── README.md
```

## Architecture

The Cybersec Agent uses a specialized architecture with intelligent routing:

1. **General Security Questions**: Handled directly by the local AI model
2. **Vulnerability & Compliance Questions**: Automatically routed to Judge via MCP

### Judge Integration

When the agent detects questions about:
- CVE vulnerabilities
- Compliance frameworks (SOC 2, GDPR, HIPAA, PCI-DSS, etc.)
- CVSS scoring
- Security audits and controls

It automatically forwards these to Judge (https://judge.mindhive.tech) for expert responses.

## API Usage

### Web Interface
Visit https://cybersec.mindhive.tech to use the interactive chat interface.

### API Endpoint
```bash
POST https://cybersec.mindhive.tech/api/ask
Content-Type: application/json

{
  "question": "What are the OWASP Top 10 vulnerabilities?"
}
```

Example with curl:
```bash
curl -X POST https://cybersec.mindhive.tech/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "How can I secure my home network?"}'
```

## Development

### Prerequisites
- Node.js and npm
- Cloudflare account
- Cloudflare API token with appropriate permissions

### Local Development
```bash
npm install
npm run dev
```

### Deployment
1. Set up your Cloudflare API token:
   ```bash
   export CLOUDFLARE_API_TOKEN="your-token-here"
   ```

2. Run the deployment script:
   ```bash
   ./scripts/deploy-all.sh
   ```

## Configuration

Edit `wrangler.toml` to adjust:
- `MAX_TOKENS`: Maximum response length (default: 512)
- `TEMPERATURE`: AI creativity level (default: 0.3)
- `JUDGE_URL`: URL of the Judge service (default: https://judge.mindhive.tech)

## Example Questions

- What are the OWASP Top 10 vulnerabilities?
- How can I secure my home network?
- What is the difference between encryption and hashing?
- How do I respond to a ransomware attack?
- What are best practices for password management?

## License

Built with ❤️ for MindHive.tech