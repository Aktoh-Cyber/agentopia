/**
 * Test suite for the InfoSec Supervisor agent.
 *
 * The InfoSec agent is a JavaScript Cloudflare Worker that acts as a
 * supervisor/router. It overrides processQuestion to analyse incoming
 * questions and suggest which specialist (Judge, Scout, Lancer, Shield)
 * should handle them, based on keyword matching. It appends a routing
 * suggestion to the AI response.
 *
 * Tests verify:
 *   - Route dispatch (same as other agents)
 *   - Keyword-based routing logic (core differentiator)
 *   - Response format with routing suggestions
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

// Routing keywords mirror the infosec agent's processQuestion override
const routingKeywords = {
  judge: ['cve', 'vulnerability', 'compliance', 'nist', 'soc2', 'gdpr', 'pci', 'iso27001', 'cvss', 'audit'],
  scout: ['recon', 'osint', 'discovery', 'intelligence', 'footprint', 'enumerate', 'scan'],
  lancer: ['pentest', 'penetration', 'exploit', 'red team', 'attack', 'offensive', 'payload'],
  shield: ['incident', 'response', 'hunting', 'defense', 'blue team', 'detection', 'siem', 'monitor'],
};

function scoreSuggestion(question) {
  const lower = question.toLowerCase();
  let maxScore = 0;
  let suggested = null;
  for (const [agent, keywords] of Object.entries(routingKeywords)) {
    const score = keywords.filter(kw => lower.includes(kw)).length;
    if (score > maxScore) {
      maxScore = score;
      suggested = agent;
    }
  }
  return suggested;
}

function createInfoSecHandler() {
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
        return new Response('<html>InfoSec Supervisor</html>', {
          headers: { 'Content-Type': 'text/html', ...corsHeaders },
        });
      }

      if (request.method === 'POST' && url.pathname === '/mcp') {
        try {
          const body = await request.json();

          if (body.method === 'tools/list') {
            return new Response(JSON.stringify({
              tools: [{
                name: 'infosec_supervisor',
                description: 'Security operations supervisor that routes questions to specialist agents',
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
                { role: 'system', content: 'You are the InfoSec Supervisor.' },
                { role: 'user', content: `Question: ${question}` },
              ],
            });
            let answer = aiResp.response;
            const suggested = scoreSuggestion(question);
            if (suggested) {
              answer += `\n\n[Routing suggestion: This question may be best handled by the ${suggested.toUpperCase()} specialist agent at https://${suggested}.aktohcyber.com]`;
            }
            return new Response(JSON.stringify({
              content: [{ type: 'text', text: answer }],
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
              { role: 'system', content: 'You are the InfoSec Supervisor.' },
              { role: 'user', content: `Question: ${question}` },
            ],
          });
          let answer = aiResp.response;
          const suggested = scoreSuggestion(question);
          if (suggested) {
            answer += `\n\n[Routing suggestion: This question may be best handled by the ${suggested.toUpperCase()} specialist agent at https://${suggested}.aktohcyber.com]`;
          }
          return new Response(JSON.stringify({ answer, cached: false }), {
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

describe('InfoSec Supervisor Agent', () => {
  let handler;
  let env;

  beforeEach(() => {
    handler = createInfoSecHandler();
    env = createMockEnv();
  });

  // ── Route dispatch ─────────────────────────────────────────────────────

  describe('Route dispatch', () => {
    it('serves homepage on GET /', async () => {
      const req = buildRequest('/', { method: 'GET' });
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(200);
      expect(res.headers.get('Content-Type')).toBe('text/html');
    });

    it('handles OPTIONS preflight', async () => {
      const req = buildRequest('/api/ask', { method: 'OPTIONS' });
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(200);
      expect(res.headers.get('Access-Control-Allow-Origin')).toBe('*');
    });

    it('returns 404 for unknown path', async () => {
      const req = buildRequest('/admin', { method: 'GET' });
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(404);
    });
  });

  // ── Routing logic (core feature) ──────────────────────────────────────

  describe('Routing logic', () => {
    it('suggests Judge for vulnerability questions', async () => {
      env.AI = createMockAI('Here is info about CVE-2021-44228');
      const req = buildAskRequest('Tell me about CVE-2021-44228 vulnerability');
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.answer).toContain('[Routing suggestion');
      expect(data.answer).toContain('JUDGE');
      expect(data.answer).toContain('judge.aktohcyber.com');
    });

    it('suggests Scout for recon questions', async () => {
      env.AI = createMockAI('OSINT techniques include...');
      const req = buildAskRequest('How do I do OSINT recon on a target?');
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.answer).toContain('SCOUT');
    });

    it('suggests Lancer for pentest questions', async () => {
      env.AI = createMockAI('Pentest methodology...');
      const req = buildAskRequest('How do I run a pentest to find exploits?');
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.answer).toContain('LANCER');
    });

    it('suggests Shield for incident response questions', async () => {
      env.AI = createMockAI('Incident response steps...');
      const req = buildAskRequest('How do I handle an incident response and detection?');
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.answer).toContain('SHIELD');
    });

    it('does not add routing suggestion for general questions', async () => {
      env.AI = createMockAI('General security advice');
      const req = buildAskRequest('What is cybersecurity?');
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.answer).not.toContain('[Routing suggestion');
    });

    it('picks the agent with the highest keyword score', async () => {
      env.AI = createMockAI('Multiple keywords');
      // "compliance" + "audit" + "nist" = 3 hits for Judge
      // "scan" = 1 hit for Scout
      const req = buildAskRequest('I need a compliance audit for nist and want to scan');
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.answer).toContain('JUDGE');
    });
  });

  // ── Error handling ────────────────────────────────────────────────────

  describe('Error handling', () => {
    it('returns 400 for empty question', async () => {
      const req = buildAskRequest('');
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(400);
    });

    it('returns 500 on AI error', async () => {
      env.AI = { run: async () => { throw new Error('AI down'); } };
      const req = buildAskRequest('test');
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(500);
    });
  });

  // ── Rate limiting ────────────────────────────────────────────────────

  describe('Rate limiting', () => {
    it('returns 429 when exceeded', async () => {
      env.RATE_LIMITER = createMockRateLimiter(false);
      const req = buildAskRequest('test');
      const res = await handler.fetch(req, env);
      expect(res.status).toBe(429);
    });
  });

  // ── MCP protocol ────────────────────────────────────────────────────

  describe('MCP protocol', () => {
    it('lists infosec_supervisor tool', async () => {
      const req = buildMCPRequest('tools/list');
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.tools[0].name).toBe('infosec_supervisor');
    });

    it('includes routing suggestion in MCP tool call response', async () => {
      env.AI = createMockAI('Compliance info');
      const req = buildMCPRequest('tools/call', {
        name: 'infosec_supervisor',
        arguments: { question: 'What are GDPR compliance requirements?' },
      });
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.content[0].text).toContain('JUDGE');
    });

    it('returns error for missing question', async () => {
      const req = buildMCPRequest('tools/call', {
        name: 'infosec_supervisor',
        arguments: {},
      });
      const res = await handler.fetch(req, env);
      const data = await parseJSON(res);
      expect(data.error.code).toBe(-32602);
    });
  });
});
