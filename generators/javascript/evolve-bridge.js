/**
 * Evolve Edge Bridge - Routes tool calls to Synapse nodes via the Evolve Edge Bridge.
 *
 * When an agent encounters a tool name matching Evolve patterns (synapse_*, evolve_*,
 * node.*), the request is forwarded as MCP JSON-RPC 2.0 to the Evolve Edge Bridge
 * Cloudflare Worker instead of being handled locally.
 *
 * Environment variables required:
 *   EVOLVE_BRIDGE_URL     - URL of the Evolve Edge Bridge worker (e.g. https://edge-bridge.evolve.workers.dev)
 *   EVOLVE_SERVICE_TOKEN  - Bearer token for service-to-service auth
 *
 * Optional:
 *   EVOLVE_LLM_ROUTER_URL  - URL of the Evolve LLM Router worker
 *   EVOLVE_TRACE_ENABLED   - Enable trace header propagation ("true" / "false")
 */

/**
 * Default glob patterns that indicate a tool call should be routed to Evolve.
 * These match the patterns defined in evolve-bridge-tool.json.
 */
const DEFAULT_EVOLVE_PATTERNS = ['synapse_*', 'evolve_*', 'node.*'];

/**
 * Converts a glob-style pattern (e.g. "synapse_*") into a RegExp.
 *
 * @param {string} pattern - Glob pattern with * wildcards
 * @returns {RegExp}
 */
function patternToRegex(pattern) {
  const escaped = pattern
    .replace(/[.+^${}()|[\]\\]/g, '\\$&')
    .replace(/\*/g, '.*');
  return new RegExp(`^${escaped}$`);
}

/**
 * Checks whether a tool name matches any Evolve routing patterns.
 *
 * @param {string} toolName - The MCP tool name to check
 * @param {string[]} [patterns] - Glob patterns to match against
 * @returns {boolean}
 */
export function matchesEvolvePattern(toolName, patterns = DEFAULT_EVOLVE_PATTERNS) {
  return patterns.some(pattern => patternToRegex(pattern).test(toolName));
}

/**
 * Builds the cross-system HTTP headers required by the Evolve Edge Bridge.
 *
 * @param {string} agentId - The calling Agentopia agent identifier
 * @param {string} requestId - Unique request ID for correlation
 * @param {string} [traceId] - Optional OpenTelemetry trace ID
 * @returns {Record<string, string>}
 */
export function buildBridgeHeaders(agentId, requestId, traceId) {
  const headers = {
    'X-Agentopia-Agent': agentId,
    'X-Request-Id': requestId,
  };

  if (traceId) {
    headers['X-Evolve-Trace-Id'] = traceId;
  }

  return headers;
}

/**
 * Routes an MCP JSON-RPC 2.0 request through the Evolve Edge Bridge.
 *
 * On bridge failure, returns null so callers can fall back to local handling.
 *
 * @param {object} mcpRequest - MCP JSON-RPC 2.0 request body
 * @param {object} env - Cloudflare Worker env bindings
 * @param {object} [options]
 * @param {string} [options.agentId] - Agent identifier for headers
 * @param {number} [options.timeoutMs] - Request timeout in milliseconds (default: 30000)
 * @returns {Promise<object|null>} MCP response body, or null on failure
 */
export async function routeViaEvolveBridge(mcpRequest, env, options = {}) {
  const bridgeUrl = env.EVOLVE_BRIDGE_URL;
  const serviceToken = env.EVOLVE_SERVICE_TOKEN;

  if (!bridgeUrl || !serviceToken) {
    console.warn('Evolve bridge not configured: missing EVOLVE_BRIDGE_URL or EVOLVE_SERVICE_TOKEN');
    return null;
  }

  const agentId = options.agentId || 'agentopia-agent';
  const requestId = crypto.randomUUID();
  const traceEnabled = env.EVOLVE_TRACE_ENABLED === 'true';
  const traceId = traceEnabled ? crypto.randomUUID() : undefined;
  const timeoutMs = options.timeoutMs || 30000;

  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${serviceToken}`,
    ...buildBridgeHeaders(agentId, requestId, traceId),
  };

  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  try {
    const response = await fetch(`${bridgeUrl}/mcp`, {
      method: 'POST',
      headers,
      body: JSON.stringify(mcpRequest),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      console.error(`Evolve bridge returned HTTP ${response.status}: ${response.statusText}`);
      return null;
    }

    return await response.json();
  } catch (error) {
    clearTimeout(timeoutId);
    console.error('Evolve bridge call failed:', error.message || error);
    return null;
  }
}

/**
 * EvolveBridgeClient wraps the Evolve Edge Bridge as a tool endpoint
 * compatible with Agentopia's DynamicMCPClient pattern.
 *
 * Usage:
 *   const bridge = new EvolveBridgeClient(env);
 *   if (bridge.isConfigured() && bridge.canHandle(toolName)) {
 *     const result = await bridge.callTool(toolName, args);
 *   }
 */
export class EvolveBridgeClient {
  /**
   * @param {object} env - Cloudflare Worker env bindings
   * @param {object} [config]
   * @param {string[]} [config.patterns] - Tool name patterns to intercept
   * @param {number} [config.timeoutMs] - Request timeout
   * @param {string} [config.agentId] - Agent identifier for tracing
   */
  constructor(env, config = {}) {
    this.env = env;
    this.patterns = config.patterns || DEFAULT_EVOLVE_PATTERNS;
    this.timeoutMs = config.timeoutMs || 30000;
    this.agentId = config.agentId || 'agentopia-agent';
  }

  /**
   * Returns true if the required environment variables are set.
   * @returns {boolean}
   */
  isConfigured() {
    return Boolean(this.env.EVOLVE_BRIDGE_URL && this.env.EVOLVE_SERVICE_TOKEN);
  }

  /**
   * Returns true if the given tool name matches Evolve routing patterns.
   * @param {string} toolName
   * @returns {boolean}
   */
  canHandle(toolName) {
    return matchesEvolvePattern(toolName, this.patterns);
  }

  /**
   * Calls a tool via the Evolve Edge Bridge using MCP JSON-RPC 2.0.
   *
   * @param {string} toolName - The tool to invoke (e.g. "synapse_nmap_scan")
   * @param {object} args - Tool arguments
   * @returns {Promise<{answer: string, source: string, toolId: string}|null>}
   */
  async callTool(toolName, args) {
    const mcpRequest = {
      jsonrpc: '2.0',
      id: crypto.randomUUID(),
      method: 'tools/call',
      params: {
        name: toolName,
        arguments: args,
      },
    };

    const result = await routeViaEvolveBridge(mcpRequest, this.env, {
      agentId: this.agentId,
      timeoutMs: this.timeoutMs,
    });

    if (!result) {
      return null;
    }

    // Handle MCP error responses
    if (result.error) {
      console.error(`Evolve bridge tool error: ${result.error.message}`);
      return null;
    }

    // Extract text content from MCP response
    const content = result.result?.content || result.content;
    if (content && Array.isArray(content) && content.length > 0 && content[0].type === 'text') {
      return {
        answer: content[0].text,
        source: `Evolve Bridge (${toolName})`,
        toolId: `evolve:${toolName}`,
      };
    }

    // Return raw result if format is unexpected
    if (result.result) {
      return {
        answer: typeof result.result === 'string' ? result.result : JSON.stringify(result.result),
        source: `Evolve Bridge (${toolName})`,
        toolId: `evolve:${toolName}`,
      };
    }

    return null;
  }

  /**
   * Lists tools available through the Evolve Edge Bridge.
   *
   * @returns {Promise<object[]|null>} Array of tool definitions, or null on failure
   */
  async listTools() {
    const mcpRequest = {
      jsonrpc: '2.0',
      id: crypto.randomUUID(),
      method: 'tools/list',
      params: {},
    };

    const result = await routeViaEvolveBridge(mcpRequest, this.env, {
      agentId: this.agentId,
      timeoutMs: this.timeoutMs,
    });

    if (!result) {
      return null;
    }

    return result.result?.tools || result.tools || null;
  }
}
