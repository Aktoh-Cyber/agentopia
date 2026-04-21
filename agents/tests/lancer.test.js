/**
 * Test suite for the Lancer agent — Red Team & Penetration Testing Expert.
 *
 * Lancer is a JavaScript Cloudflare Worker specialist agent handling
 * offensive security, pen testing, exploit development, and red team ops.
 * It extends BaseAgent without overriding processQuestion.
 *
 * Tests verify:
 *   - Route dispatch
 *   - Response format and headers
 *   - Error handling
 *   - Rate limiting
 *   - MCP protocol compliance
 */

import { describe, it, expect, beforeEach } from 'vitest';
import {
  createMockEnv,
  createMockAI,
  createMockRateLimiter,
  buildRequest,
  buildAskRequest,
  buildMCPRequest,
  parseJSON,
} from './helpers.js';

function createLancerHandler() {
  return {
    async fetch(request, env) {
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

      if (request.method === 'OPTIONS') {
        return new Response(null, { headers: corsHeaders });
      }

      if (request.method === 'GET' && url.pathname === '/') {
        return new Response('<html>Lancer</html>', {
          headers: { 'Content-Type': 'text/html', ...corsHeaders },
        });
      }

      if (request.method === 'POST' && url.pathname === '/mcp') {
        try {
          const body = await request.json();

          if (body.method === 'tools/list') {
            return new Response(JSON.stringify({
              tools: [{
                name: 'lancer_red_team_pentest',
                description: 'Specialized AI for offensive security, red teaming, and penetration testing methodologies',
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
                { role: 'system', content: 'You are a specialized offensive security expert.' },
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
              { role: 'system', content: 'You are a specialized offensive security expert.' },
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

describe('Lancer Agent', () => {
  let handler;
  let env;

  beforeEach(() => {
    handler = createLancerHandler();
    env = createMockEnv();
  });

  describe('Route dispatch', () => {
    it('returns HTML homepage on GET /', async () => {
      const req = buildRequest('/', { method: 'GET' });
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(200);
      expect(res.headers.get('Content-Type')).toBe('text/html');
    });

    it('returns CORS headers on OPTIONS', async () => {
      const req = buildRequest('/', { method: 'OPTIONS' });
      const res = await handler.fetch(req, env);
      expect(res.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    it('returns 404 for unknown routes', async () => {
      const req = buildRequest('/does-not-exist', { method: 'POST', body: '{}' });
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(404);
    });
  });

  describe('POST /api/ask', () => {
    it('returns answer for a pentest question', async () => {
      env.AI = createMockAI('Use Metasploit for exploitation');
      const req = buildAskRequest('What tools are used in penetration testing?');
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(200);
      const data = await parseJSON(res);
      expect(data.answer).toBe('Use Metasploit for exploitation');
      expect(data.cached).toBe(false);
    });

    it('returns 400 for missing question', async () => {
      const req = buildRequest('/api/ask', {
        method: 'POST',
        body: JSON.stringify({}),
      });
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(400);
    });

    it('returns 500 on AI failure', async () => {
      env.AI = { run: async () => { throw new Error('boom'); } };
      const req = buildAskRequest('anything');
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(500);
    });

    it('includes CORS headers', async () => {
      const req = buildAskRequest('test');
      const res = await handler.fetch(req, env);
      expect(res.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });
  });

  describe('Rate limiting', () => {
    it('returns 429 when rate limit is exceeded', async () => {
      env.RATE_LIMITER = createMockRateLimiter(false);
      const req = buildAskRequest('test');
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(429);
      expect(res.headers.get('Retry-After')).toBe('60');
    });
  });

  describe('MCP protocol', () => {
    it('lists lancer tool on tools/list', async () => {
      const req = buildMCPRequest('tools/list');
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.tools).toHaveLength(1);
      expect(data.tools[0].name).toBe('lancer_red_team_pentest');
    });

    it('processes tools/call with a valid question', async () => {
      env.AI = createMockAI('Privilege escalation via kernel exploit');
      const req = buildMCPRequest('tools/call', {
        name: 'lancer_red_team_pentest',
        arguments: { question: 'How to escalate privileges on Linux?' },
      });
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.content[0].type).toBe('text');
      expect(data.content[0].text).toContain('kernel exploit');
    });

    it('returns error for tools/call without question', async () => {
      const req = buildMCPRequest('tools/call', {
        name: 'lancer_red_team_pentest',
        arguments: {},
      });
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.error.code).toBe(-32602);
    });

    it('returns method-not-found for bad MCP method', async () => {
      const req = buildMCPRequest('resources/list');
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.error.code).toBe(-32601);
    });
  });
});
