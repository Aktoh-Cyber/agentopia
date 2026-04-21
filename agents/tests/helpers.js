/**
 * Shared test helpers and mocks for Agentopia agent tests.
 *
 * All JS agents run on Cloudflare Workers and share the same base-agent.js
 * framework. These helpers provide mock objects that simulate the Workers
 * runtime environment (env.AI, env.CACHE, env.RATE_LIMITER, Request/Response).
 */

/**
 * Create a mock Cloudflare Workers AI binding.
 * @param {string} [responseText] - The text the mock AI should return.
 * @returns {object} A mock AI binding with a `.run()` method.
 */
export function createMockAI(responseText = 'Mock AI response') {
  return {
    run: async (_model, params) => ({
      response: responseText,
    }),
  };
}

/**
 * Create a mock KV namespace (used for CACHE binding).
 * @returns {object} A mock KV binding with get/put/delete.
 */
export function createMockCache() {
  const store = new Map();
  return {
    get: async (key) => store.get(key) ?? null,
    put: async (key, value, _opts) => { store.set(key, value); },
    delete: async (key) => { store.delete(key); },
    _store: store,
  };
}

/**
 * Create a mock rate limiter binding.
 * @param {boolean} [allow=true] - Whether to allow the request.
 * @returns {object}
 */
export function createMockRateLimiter(allow = true) {
  return {
    limit: async (_opts) => ({ success: allow }),
  };
}

/**
 * Build a standard mock `env` object for testing agents.
 * @param {object} [overrides] - Override specific bindings.
 * @returns {object}
 */
export function createMockEnv(overrides = {}) {
  return {
    AI: createMockAI(),
    CACHE: createMockCache(),
    RATE_LIMITER: createMockRateLimiter(true),
    ...overrides,
  };
}

/**
 * Build a Request object suitable for the Workers fetch handler.
 * @param {string} path - URL path, e.g. '/api/ask'
 * @param {object} [options] - Extra RequestInit options.
 * @returns {Request}
 */
export function buildRequest(path, options = {}) {
  const url = `https://test.aktohcyber.com${path}`;
  const defaults = {
    headers: {
      'Content-Type': 'application/json',
      'cf-connecting-ip': '127.0.0.1',
    },
  };
  return new Request(url, { ...defaults, ...options });
}

/**
 * Build a POST /api/ask request with a question body.
 * @param {string} question
 * @returns {Request}
 */
export function buildAskRequest(question) {
  return buildRequest('/api/ask', {
    method: 'POST',
    body: JSON.stringify({ question }),
  });
}

/**
 * Build a POST /mcp request with a given MCP method and params.
 * @param {string} method - e.g. 'tools/list' or 'tools/call'
 * @param {object} [params] - MCP params
 * @returns {Request}
 */
export function buildMCPRequest(method, params = {}) {
  return buildRequest('/mcp', {
    method: 'POST',
    body: JSON.stringify({ method, params }),
  });
}

/**
 * Parse a JSON response body.
 * @param {Response} response
 * @returns {Promise<object>}
 */
export async function parseJSON(response) {
  return response.json();
}
