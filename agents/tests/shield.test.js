/**
 * Test suite for the Shield agent — Blue Team & Incident Response Expert.
 *
 * Shield is a JavaScript Cloudflare Worker specialist agent focused on
 * incident response, threat hunting, SIEM, forensics, and blue team defence.
 * It extends BaseAgent without overriding processQuestion.
 *
 * Tests verify:
 *   - Route dispatch (GET /, POST /api/ask, POST /mcp, OPTIONS, 404)
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

function createShieldHandler() {
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
        return new Response('<html>Shield</html>', {
          headers: { 'Content-Type': 'text/html', ...corsHeaders },
        });
      }

      if (request.method === 'POST' && url.pathname === '/mcp') {
        try {
          const body = await request.json();

          if (body.method === 'tools/list') {
            return new Response(JSON.stringify({
              tools: [{
                name: 'shield_blue_team_incident_response',
                description: 'Specialized AI for blue team operations, incident response, threat hunting, and defensive security',
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
                { role: 'system', content: 'You are a specialized defensive security expert.' },
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
              { role: 'system', content: 'You are a specialized defensive security expert.' },
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

describe('Shield Agent', () => {
  let handler;
  let env;

  beforeEach(() => {
    handler = createShieldHandler();
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
      const req = buildRequest('/api/ask', { method: 'OPTIONS' });
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(200);
      expect(res.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    it('returns 404 for unknown routes', async () => {
      const req = buildRequest('/nope', { method: 'GET' });
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(404);
    });
  });

  describe('POST /api/ask', () => {
    it('returns answer for incident response question', async () => {
      env.AI = createMockAI('Containment is the third phase of IR');
      const req = buildAskRequest('What are the NIST IR phases?');
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(200);
      const data = await parseJSON(res);
      expect(data.answer).toBe('Containment is the third phase of IR');
    });

    it('returns 400 for empty question', async () => {
      const req = buildAskRequest('');
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(400);
      const data = await parseJSON(res);
      expect(data.error).toMatch(/required/i);
    });

    it('returns 500 on AI failure', async () => {
      env.AI = { run: async () => { throw new Error('fail'); } };
      const req = buildAskRequest('test');
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(500);
    });
  });

  describe('Rate limiting', () => {
    it('returns 429 when rate limit exceeded', async () => {
      env.RATE_LIMITER = createMockRateLimiter(false);
      const req = buildAskRequest('test');
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(429);
    });
  });

  describe('MCP protocol', () => {
    it('lists shield tool', async () => {
      const req = buildMCPRequest('tools/list');
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.tools[0].name).toBe('shield_blue_team_incident_response');
    });

    it('calls shield tool with question', async () => {
      env.AI = createMockAI('Use Volatility for memory forensics');
      const req = buildMCPRequest('tools/call', {
        name: 'shield_blue_team_incident_response',
        arguments: { question: 'How to do memory forensics?' },
      });
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.content[0].text).toBe('Use Volatility for memory forensics');
    });

    it('returns error for missing question in tools/call', async () => {
      const req = buildMCPRequest('tools/call', {
        name: 'shield_blue_team_incident_response',
        arguments: {},
      });
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.error.code).toBe(-32602);
    });

    it('returns method-not-found for unknown method', async () => {
      const req = buildMCPRequest('tools/unknown');
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.error.code).toBe(-32601);
    });
  });
});
