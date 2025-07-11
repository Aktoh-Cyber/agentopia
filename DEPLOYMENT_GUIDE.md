# Agent Generator Deployment Guide

This guide walks through deploying the complete GitOps Agent Generation system.

## 🚀 Quick Start

### 1. Prerequisites

- Cloudflare account with Workers Paid plan
- GitHub account with Personal Access Token
- Node.js 18+ and npm installed
- `wrangler` CLI installed globally: `npm install -g wrangler`

### 2. Configure Cloudflare

```bash
# Login to Cloudflare
wrangler auth login

# Get your account and zone IDs
wrangler whoami
```

### 3. Setup GitHub Integration

Create a GitHub Personal Access Token with these permissions:
- `repo` (Full control of private repositories)
- `workflow` (Update GitHub Action workflows)

### 4. Deploy Agent Generator

```bash
# Navigate to the generated agent
cd agent-generator-test/generator

# Update wrangler.toml with your IDs
# Edit: account_id, zone_id, GITHUB_REPO_OWNER, GITHUB_REPO_NAME

# Set GitHub token as secret
wrangler secret put GITHUB_TOKEN
# Enter your GitHub Personal Access Token when prompted

# Deploy the agent
wrangler deploy
```

### 5. Configure GitHub Repository

Add these secrets to your GitHub repository:
- `CLOUDFLARE_API_TOKEN`: Your Cloudflare API token

Enable GitHub Actions in your repository settings.

## 📋 Complete Architecture

### Repository Structure

```
agent-framework/
├── generators/                    # Language-specific generators
│   ├── javascript/               # JavaScript generator
│   └── python/                   # Python generator (with GeneratorAgent)
├── generated-agents/             # Auto-generated agents
│   ├── router-agents/           # Router agents
│   └── specialist-agents/       # Specialist agents  
├── .github/workflows/           # CI/CD automation
│   ├── deploy-agents.yml       # Deploy new/updated agents
│   └── cleanup-agents.yml      # Remove deleted agents
└── agent-generator-test/        # Agent Generator deployment
    └── generator/               # The main generator agent
```

### Workflow Process

1. **User Request**: Access Agent Generator web UI
2. **Configuration**: Fill out agent requirements form
3. **Generation**: System creates all agent files
4. **GitHub Commit**: Files committed to feature branch
5. **Pull Request**: Auto-created PR with validation
6. **CI/CD Pipeline**: GitHub Actions validate and test
7. **Deployment**: Merge triggers deployment to Cloudflare
8. **Live Agent**: Agent available at specified domain

## 🔧 Configuration Examples

### Environment Variables (wrangler.toml)

```toml
[vars]
MAX_TOKENS = "1024"
TEMPERATURE = "0.2"
GITHUB_REPO_OWNER = "your-username"
GITHUB_REPO_NAME = "agent-framework"

# Secrets (set with wrangler secret put)
# GITHUB_TOKEN = "ghp_your_token_here"
```

### Agent Configuration Example

```json
{
  "type": "specialist",
  "name": "Threat Intelligence Expert", 
  "description": "AI specialist for threat analysis",
  "domain": "threat-intel.yourdomain.com",
  "systemPrompt": "You are a threat intelligence expert...",
  "expertise": "threat intelligence and IOC analysis",
  "keywords": ["threat", "intel", "ioc", "malware"],
  "accountId": "your-cloudflare-account-id",
  "zoneId": "your-cloudflare-zone-id"
}
```

## 🛠️ Development Workflow

### Creating a New Agent

1. **Access Generator**: Navigate to `https://generator.yourdomain.com`
2. **Configure Agent**: Fill out the web form
3. **Generate**: Click "🚀 Generate Agent"
4. **Review PR**: Check the auto-created pull request
5. **Merge**: Approve and merge to deploy

### Updating Existing Agent

1. **Modify Config**: Update the agent's configuration
2. **Regenerate**: Use the generator to create updated version
3. **Auto-Replace**: System replaces existing agent files
4. **Deploy**: Standard CI/CD process deploys updates

### Removing Agents

1. **Delete Files**: Remove agent directory from `generated-agents/`
2. **Commit**: Commit the deletion
3. **Auto-Cleanup**: Cleanup workflow removes Cloudflare resources

## 🔍 Monitoring and Debugging

### GitHub Actions Logs

- **Deploy Workflow**: Monitor agent deployments
- **Cleanup Workflow**: Track agent removals
- **Validation**: Check configuration validation

### Cloudflare Dashboard

- **Workers**: Monitor deployed agents
- **Analytics**: View usage and performance
- **Logs**: Debug runtime issues

### Agent Generator Logs

- **MCP Calls**: Monitor agent generation requests
- **GitHub API**: Track repository interactions
- **Validation**: Check configuration errors

## 🚨 Troubleshooting

### Common Issues

**GitHub Token Issues**
```bash
# Verify token permissions
curl -H "Authorization: token $GITHUB_TOKEN" https://api.github.com/user

# Update token
wrangler secret put GITHUB_TOKEN
```

**Deployment Failures**
```bash
# Check wrangler configuration
wrangler whoami

# Validate configuration
npx wrangler deploy --dry-run
```

**Agent Generation Errors**
- Check required fields in configuration
- Verify GitHub repository exists
- Confirm Cloudflare IDs are correct

### Debug Mode

Enable debug logging by setting environment variables:

```bash
# In wrangler.toml [vars]
DEBUG = "true"
LOG_LEVEL = "debug"
```

## 🎯 Best Practices

### Security

- Use GitHub secrets for sensitive data
- Rotate API tokens regularly
- Review generated code before deployment
- Use branch protection rules

### Performance

- Cache agent responses appropriately
- Monitor Worker execution times
- Use appropriate resource limits
- Implement rate limiting

### Maintenance

- Regular dependency updates
- Monitor GitHub API rate limits
- Clean up unused branches
- Review generated agent metrics

## 📚 Additional Resources

- [Cloudflare Workers Documentation](https://developers.cloudflare.com/workers/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Model Context Protocol](https://github.com/modelcontextprotocol)
- [Pyodide Documentation](https://pyodide.org/)

---

*For support, create an issue in the repository or contact the development team.*