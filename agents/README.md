# Agents Directory

Pre-built agent implementations and framework components for the Agentopia platform.

## Purpose

Contains the BaseAgent framework, code generators, and pre-built specialist agents that deploy to Cloudflare Workers.

## Structure

| Directory | Description |
|-----------|-------------|
| `agent-framework/` | Core `BaseAgent` class providing CORS, caching, AI calls, and MCP server functionality (JS) |
| `agent-generator/` | Agent code generation from JSON config (JS, with wrangler deployment support) |
| `cybersec-agent/` | Generic cybersecurity specialist agent |
| `infosec/` | InfoSec domain specialist agent |
| `judge/` | Vulnerability assessment and compliance specialist |
| `judge-js/` | JavaScript implementation of Judge agent |
| `lancer/` | Red team / attack simulation specialist |
| `scout/` | Reconnaissance and network discovery specialist |
| `shield/` | Defense and incident response specialist |
| `tests/` | Shared test utilities |

## How It Works

1. `agent-framework/base-agent.js` provides the foundation: CORS handling, Cloudflare AI calls, MCP protocol support, caching, and conversation memory
2. Each specialist agent extends BaseAgent with domain-specific system prompts, keywords, and patterns
3. `agent-generator/` builds deployable agents from JSON configuration files using templates

## Key Concepts

- **BaseAgent**: Handles HTTP routing, AI model invocation (via Cloudflare Workers AI), and MCP tool exposure
- **RouterAgent**: Extends BaseAgent to route queries to specialist agents using ToolRegistry scoring
- **ToolRegistry**: Dynamic routing with keyword matching (+1 point), regex patterns (+2 points), and priority multipliers
