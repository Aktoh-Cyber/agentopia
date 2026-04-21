# Deployment Directory

Infrastructure and deployment tooling for Agentopia agents on Cloudflare Workers.

## Purpose

Provides Pulumi IaC, deployment scripts, and configuration for deploying generated agents to Cloudflare Workers.

## Structure

| Path | Description |
|------|-------------|
| `deploy.sh` | Main deployment script. Checks prerequisites (Pulumi, Node.js, Cloudflare API token), then deploys all agents via Pulumi. |
| `setup.sh` | Environment setup and initial configuration |
| `configs/` | Per-agent deployment configurations (judge, scout, lancer, shield, infosec-supervisor) |
| `pulumi/` | Pulumi TypeScript project for Cloudflare Workers infrastructure |
| `generated-agents/` | Output directory for generated agent code ready for deployment |

## Prerequisites

- Pulumi CLI installed
- Node.js installed
- `CLOUDFLARE_API_TOKEN` environment variable set

## Usage

```bash
# Set up environment
export CLOUDFLARE_API_TOKEN="your-token"

# Deploy all agents
./deploy.sh

# Or deploy via Pulumi directly
cd pulumi && pulumi up
```

## Pulumi Stack

The `pulumi/` directory contains:
- `index.ts` - Infrastructure definition for Cloudflare Workers
- `Pulumi.yaml` - Pulumi project configuration
- Worker routes, KV namespaces, and custom domains for each agent
