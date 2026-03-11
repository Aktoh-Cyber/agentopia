# Evolve Edge Bridge Integration

This document describes how Agentopia agents route tool calls to Synapse nodes via the Evolve Edge Bridge.

## Overview

The Evolve Edge Bridge is a Cloudflare Worker that accepts MCP JSON-RPC 2.0 requests and forwards them to the Synapse distributed fabric. When an Agentopia agent encounters a tool name matching Evolve patterns (`synapse_*`, `evolve_*`, `node.*`), the request is automatically routed through the bridge instead of being handled locally.

## Architecture

```
Agentopia Agent (Router/Specialist)
  |
  |-- ToolRegistry.findToolForQuestion()
  |     |-- matches "evolve-bridge" tool entry?
  |           |-- YES --> EvolveBridgeClient.callTool()
  |           |            |-- POST {EVOLVE_BRIDGE_URL}/mcp
  |           |            |    Authorization: Bearer {EVOLVE_SERVICE_TOKEN}
  |           |            |    X-Agentopia-Agent: {agent-id}
  |           |            |    X-Request-Id: {uuid}
  |           |            |-- Synapse node processes request
  |           |            |-- Returns MCP JSON-RPC 2.0 response
  |           |
  |           |-- NO --> Standard MCP call to specialist endpoint
  |
  |-- Direct MCP tools/call for synapse_* tool?
        |-- YES --> EvolveBridgeClient.callTool()
        |-- NO  --> Standard handleMCPToolCall()
```

## Files Added/Modified

### New Files

| File | Purpose |
|------|---------|
| `generators/javascript/evolve-bridge.js` | Bridge routing module: pattern matching, header building, HTTP client, EvolveBridgeClient class |
| `generators/javascript/configs/evolve-bridge-tool.json` | Tool registry config for the Evolve Edge Bridge |
| `generators/javascript/configs/evolve-llm-router.json` | Tool registry config for the Evolve LLM Router |

### Modified Files

| File | Change |
|------|--------|
| `generators/javascript/tool-registry.js` | Added `import` of EvolveBridgeClient; Extended DynamicMCPClient with `initEvolveBridge()` and `askEvolveTool()` methods |
| `generators/javascript/router-agent.js` | Initializes Evolve bridge in `setupLangChainComponents()` and `processQuestionLegacy()`; Routes Evolve-pattern MCP tool calls in `handleMCPToolCall()`; Advertises Synapse tools in `handleMCPToolsList()` |
| `generators/javascript/configs/infosec-router.json` | Added `evolve-bridge` tool entry to the registry tools array |
| `generators/javascript/configs/infosec-supervisor.json` | Added `evolveBridge` config block and Evolve-related keywords |
| `agents/infosec/wrangler.toml` | Added Evolve env var comments and secret binding comments |
| `agents/scout/wrangler.toml` | Added Evolve env var comments and secret binding comments |

## Environment Variables

### Required (for Evolve integration)

| Variable | Description | Example |
|----------|-------------|---------|
| `EVOLVE_BRIDGE_URL` | URL of the Evolve Edge Bridge worker | `https://edge-bridge.evolve.workers.dev` |
| `EVOLVE_SERVICE_TOKEN` | Bearer token for service-to-service auth | (set via `npx wrangler secret put`) |

### Optional

| Variable | Description | Default |
|----------|-------------|---------|
| `EVOLVE_LLM_ROUTER_URL` | URL of the Evolve LLM Router worker | (none) |
| `EVOLVE_TRACE_ENABLED` | Enable trace header propagation | `false` |

## Setup Steps

### 1. Set Environment Variables

For each agent that needs Evolve routing (e.g., infosec, scout):

```bash
# In the agent's wrangler.toml, uncomment and set:
# EVOLVE_BRIDGE_URL = "https://edge-bridge.evolve.workers.dev"

# Set the service token as a secret:
cd agents/infosec
npx wrangler secret put EVOLVE_SERVICE_TOKEN
# Paste the token value when prompted
```

### 2. Register Evolve Tools (Router Agents)

For router agents, the Evolve bridge tool entry is already in `infosec-router.json`. When regenerating agents:

```bash
cd generators/javascript
node build-agent.js configs/infosec-router.json ../../agents/infosec
```

### 3. Direct MCP Tool Calls

Any MCP `tools/call` request with a tool name matching `synapse_*`, `evolve_*`, or `node.*` is automatically intercepted by the RouterAgent and forwarded through the bridge.

Example MCP request:
```json
{
  "jsonrpc": "2.0",
  "id": "1",
  "method": "tools/call",
  "params": {
    "name": "synapse_nmap_scan",
    "arguments": {
      "target": "192.168.1.0/24",
      "ports": "1-1000"
    }
  }
}
```

## Fallback Behavior

- If `EVOLVE_BRIDGE_URL` or `EVOLVE_SERVICE_TOKEN` are not set, the bridge is silently disabled
- If the bridge returns an error or times out, the system falls back to standard MCP routing
- No existing functionality is affected when the bridge is not configured

## Cross-Reference: Evolve Side

The Evolve integration source lives at:
- `evolve/integrations/agentopia/src/bridge-routing.ts` - TypeScript bridge routing (reference implementation)
- `evolve/integrations/agentopia/src/tool-registry-patch.ts` - Tool registry patch (reference)
- `evolve/integrations/agentopia/src/env-vars.ts` - Environment variable validation
- `evolve/integrations/agentopia/src/types.ts` - Shared types (McpRequest, McpResponse, EvolveBridgeConfig)
- `evolve/configs/evolve-bridge-tool.json` - Canonical bridge tool config
- `evolve/configs/evolve-llm-router.json` - Canonical LLM router config
