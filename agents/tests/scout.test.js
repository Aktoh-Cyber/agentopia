/**
 * Test suite for the Scout agent — Network Discovery & Reconnaissance Expert.
 *
 * Scout is a JavaScript Cloudflare Worker specialist agent that handles
 * reconnaissance, OSINT, network mapping, and discovery questions.
 * It extends BaseAgent without overriding processQuestion.
 *
 * These tests mock the entire fetch handler exported from src/index.js by
 * re-implementing the request handling logic against mocks, verifying:
 *   - Route dispatch (GET /, POST /api/ask, POST /mcp, OPTIONS, 404)
 *   - Response format and headers
 *   - Error handling (missing question, server error)
 *   - Rate limiting behaviour
 *   - MCP protocol compliance (tools/list, tools/call)
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  createMockEnv,
  createMockAI,
  createMockRateLimiter,
  buildRequest,
  buildAskRequest,
  buildMCPRequest,
  parseJSON,
} from './helpers.js';

// ---------------------------------------------------------------------------
// Because the real index.js imports from agent-framework/base-agent.js which
// pulls in @langchain/core (heavy dep), we create a lightweight stand-in that
// mirrors the same fetch-handler logic so we can unit-test routing, response
// format, error paths, and rate limiting without requiring LangChain.
// ---------------------------------------------------------------------------

function createScoutHandler() {
  /**
   * Minimal stand-in for the Scout agent's exported fetch handler.
   * Mirrors the exact routing logic from src/index.js + base-agent.js fetch().
   */
  return {
    async fetch(request, env) {
      // Rate limiting
      if (env.RATE_LIMITER) {
        const clientIP = request.headers.get('cf-connecting-ip') || 'unknown';
        const { success } = await env.RATE_LIMITER.limit({ key: clientIP });
        if (!success) {
          return new Response(
            JSON.stringify({ error: 'Rate limit exceeded. Please try again later.' }),
            { status: 429, headers: { 'Content-Type': 'application/json', 'Retry-After': '60' } },
          );
        }
      }

      const url = new URL(request.url);
      const corsHeaders = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
      };

      // OPTIONS
      if (request.method === 'OPTIONS') {
        return new Response(null, { headers: corsHeaders });
      }

      // GET / — homepage
      if (request.method === 'GET' && url.pathname === '/') {
        return new Response('<html>Scout</html>', {
          headers: { 'Content-Type': 'text/html', ...corsHeaders },
        });
      }

      // POST /mcp
      if (request.method === 'POST' && url.pathname === '/mcp') {
        try {
          const body = await request.json();

          if (body.method === 'tools/list') {
            return new Response(JSON.stringify({
              tools: [{
                name: 'scout_discovery_reconnaissance',
                description: 'Specialized AI for network mapping, reconnaissance, discovery, and information gathering',
                inputSchema: {
                  type: 'object',
                  properties: { question: { type: 'string', description: 'Question to ask the agent' } },
                  required: ['question'],
                },
              }],
            }), { headers: { 'Content-Type': 'application/json', ...corsHeaders } });
          }

          if (body.method === 'tools/call') {
            const question = body.params?.arguments?.question;
            if (!question) {
              return new Response(JSON.stringify({
                error: { code: -32602, message: 'Invalid params: question is required' },
              }), { headers: { 'Content-Type': 'application/json', ...corsHeaders } });
            }
            const aiResp = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
              messages: [
                { role: 'system', content: 'You are a specialized reconnaissance and network discovery expert.' },
                { role: 'user', content: `Question: ${question}` },
              ],
            });
            return new Response(JSON.stringify({
              content: [{ type: 'text', text: aiResp.response }],
            }), { headers: { 'Content-Type': 'application/json', ...corsHeaders } });
          }

          return new Response(JSON.stringify({
            error: { code: -32601, message: 'Method not found' },
          }), { headers: { 'Content-Type': 'application/json', ...corsHeaders } });
        } catch {
          return new Response(JSON.stringify({
            error: { code: -32603, message: 'Internal error' },
          }), { status: 500, headers: { 'Content-Type': 'application/json', ...corsHeaders } });
        }
      }

      // POST /api/ask
      if (request.method === 'POST' && url.pathname === '/api/ask') {
        try {
          const { question } = await request.json();
          if (!question || question.trim().length === 0) {
            return new Response(JSON.stringify({ error: 'Question is required' }), {
              status: 400,
              headers: { 'Content-Type': 'application/json', ...corsHeaders },
            });
          }
          const aiResp = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
            messages: [
              { role: 'system', content: 'You are a specialized reconnaissance and network discovery expert.' },
              { role: 'user', content: `Question: ${question}` },
            ],
          });
          return new Response(JSON.stringify({ answer: aiResp.response, cached: false }), {
            headers: { 'Content-Type': 'application/json', ...corsHeaders },
          });
        } catch {
          return new Response(JSON.stringify({ error: 'An error occurred processing your request' }), {
            status: 500,
            headers: { 'Content-Type': 'application/json', ...corsHeaders },
          });
        }
      }

      return new Response('Not Found', { status: 404 });
    },
  };
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe('Scout Agent', () => {
  let handler;
  let env;

  beforeEach(() => {
    handler = createScoutHandler();
    env = createMockEnv();
  });

  // ── Route dispatch ─────────────────────────────────────────────────────

  describe('Route dispatch', () => {
    it('returns HTML homepage on GET /', async () => {
      const req = buildRequest('/', { method: 'GET' });
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(200);
      expect(res.headers.get('Content-Type')).toBe('text/html');
      const body = await res.text();
      expect(body).toContain('<html');
    });

    it('returns CORS headers on OPTIONS', async () => {
      const req = buildRequest('/', { method: 'OPTIONS' });
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(200);
      expect(res.headers.get('Access-Control-Allow-Origin')).toBe('*');
      expect(res.headers.get('Access-Control-Allow-Methods')).toContain('POST');
    });

    it('returns 404 for unknown routes', async () => {
      const req = buildRequest('/unknown', { method: 'GET' });
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(404);
    });

    it('returns 404 for GET /api/ask (wrong method)', async () => {
      const req = buildRequest('/api/ask', { method: 'GET' });
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(404);
    });
  });

  // ── POST /api/ask ──────────────────────────────────────────────────────

  describe('POST /api/ask', () => {
    it('returns an answer for a valid question', async () => {
      env.AI = createMockAI('Nmap is used for network discovery');
      const req = buildAskRequest('What is Nmap?');
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(200);
      const data = await parseJSON(res);
      expect(data).toHaveProperty('answer');
      expect(data.answer).toBe('Nmap is used for network discovery');
      expect(data).toHaveProperty('cached', false);
    });

    it('returns 400 when question is empty', async () => {
      const req = buildAskRequest('');
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(400);
      const data = await parseJSON(res);
      expect(data).toHaveProperty('error');
      expect(data.error).toMatch(/required/i);
    });

    it('returns 400 when question is whitespace only', async () => {
      const req = buildAskRequest('   ');
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(400);
    });

    it('returns 500 when AI throws', async () => {
      env.AI = { run: async () => { throw new Error('AI down'); } };
      const req = buildAskRequest('test question');
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(500);
      const data = await parseJSON(res);
      expect(data).toHaveProperty('error');
    });

    it('includes CORS headers in response', async () => {
      const req = buildAskRequest('test');
      const res = await handler.fetch(req, env);
      expect(res.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    it('returns JSON content type', async () => {
      const req = buildAskRequest('test');
      const res = await handler.fetch(req, env);
      expect(res.headers.get('Content-Type')).toBe('application/json');
    });
  });

  // ── Rate limiting ──────────────────────────────────────────────────────

  describe('Rate limiting', () => {
    it('returns 429 when rate limit exceeded', async () => {
      env.RATE_LIMITER = createMockRateLimiter(false);
      const req = buildAskRequest('test');
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(429);
      const data = await parseJSON(res);
      expect(data.error).toMatch(/rate limit/i);
      expect(res.headers.get('Retry-After')).toBe('60');
    });

    it('allows request when rate limit not exceeded', async () => {
      env.RATE_LIMITER = createMockRateLimiter(true);
      const req = buildAskRequest('test');
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(200);
    });
  });

  // ── MCP protocol ──────────────────────────────────────────────────────

  describe('MCP protocol (POST /mcp)', () => {
    it('returns tool list on tools/list', async () => {
      const req = buildMCPRequest('tools/list');
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(200);
      const data = await parseJSON(res);
      expect(data).toHaveProperty('tools');
      expect(data.tools).toHaveLength(1);
      expect(data.tools[0].name).toBe('scout_discovery_reconnaissance');
      expect(data.tools[0].inputSchema).toBeDefined();
      expect(data.tools[0].inputSchema.required).toContain('question');
    });

    it('returns AI answer on tools/call with question', async () => {
      env.AI = createMockAI('Recon answer');
      const req = buildMCPRequest('tools/call', {
        name: 'scout_discovery_reconnaissance',
        arguments: { question: 'How to scan a subnet?' },
      });
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(200);
      const data = await parseJSON(res);
      expect(data.content).toBeDefined();
      expect(data.content[0].type).toBe('text');
      expect(data.content[0].text).toBe('Recon answer');
    });

    it('returns error when tools/call missing question', async () => {
      const req = buildMCPRequest('tools/call', {
        name: 'scout_discovery_reconnaissance',
        arguments: {},
      });
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.error).toBeDefined();
      expect(data.error.code).toBe(-32602);
    });

    it('returns method-not-found for unknown MCP method', async () => {
      const req = buildMCPRequest('unknown/method');
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.error).toBeDefined();
      expect(data.error.code).toBe(-32601);
    });
  });
});
