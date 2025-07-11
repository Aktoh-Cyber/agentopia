# Judge - Vulnerability & Compliance Expert

A specialized Cloudflare Worker AI service focused on vulnerability assessment and compliance expertise, serving both as a standalone web interface and as an MCP (Model Context Protocol) server for other agents.

🔗 **Live Demo**: https://judge.mindhive.tech

## Overview

Judge is a specialized AI assistant that provides expert knowledge on:
- CVE database and vulnerability scoring (CVSS)
- Security compliance frameworks (SOC 2, GDPR, HIPAA, PCI-DSS, ISO 27001, NIST)
- Vulnerability assessment methodologies
- Risk assessment and remediation strategies
- Compliance auditing and gap analysis

## Features

- ⚖️ **Specialized Expertise**: Deep knowledge of vulnerabilities and compliance frameworks
- 🤖 **AI-powered**: Uses Cloudflare Workers AI (Llama 3.1 8B) for accurate responses
- 🔌 **MCP Server**: Provides Model Context Protocol interface for agent-to-agent communication
- 🌐 **Web Interface**: Standalone chat interface for direct user interaction
- 📡 **RESTful API**: Traditional API endpoint for programmatic access
- ⚡ **KV Caching**: Fast responses with intelligent caching

## Architecture

Judge serves multiple interfaces:

1. **Web Interface** (`/`): Interactive chat for users
2. **REST API** (`/api/ask`): Traditional API endpoint
3. **MCP Server** (`/mcp`): Model Context Protocol interface for AI agents

## MCP Integration

Judge implements the Model Context Protocol, allowing other AI agents to query it as a specialized tool.

### MCP Endpoints

#### List Available Tools
```bash
POST https://judge.mindhive.tech/mcp
Content-Type: application/json

{
  "method": "tools/list"
}
```

#### Call Judge Tool
```bash
POST https://judge.mindhive.tech/mcp
Content-Type: application/json

{
  "method": "tools/call",
  "params": {
    "name": "judge_vulnerability_compliance",
    "arguments": {
      "question": "What is CVE-2021-44228 and how do I remediate it?"
    }
  }
}
```

## API Usage

### Web Interface
Visit https://judge.mindhive.tech to use the interactive chat interface.

### REST API Endpoint
```bash
POST https://judge.mindhive.tech/api/ask
Content-Type: application/json

{
  "question": "What are the key requirements for SOC 2 Type II compliance?"
}
```

### Example Questions

- What is CVE-2021-44228 (Log4Shell) and how do I remediate it?
- What are the key requirements for SOC 2 Type II compliance?
- How do I calculate CVSS scores for vulnerabilities?
- What are the GDPR requirements for data breach notification?
- What controls are needed for PCI-DSS compliance at Level 1?

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
- `JUDGE_URL`: URL where Judge is deployed

## Integration with Other Agents

Judge is designed to be used by other AI agents through the MCP protocol. For example, the cybersec-agent automatically routes vulnerability and compliance questions to Judge for expert responses.

## License

Built with ❤️ for MindHive.tech