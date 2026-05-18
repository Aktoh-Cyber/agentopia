# Agents Directory

Pre-built agent implementations and framework components for the Agentopia platform.

## Purpose

Contains the BaseAgent framework, code generators, and pre-built specialist agents that deploy to Cloudflare Workers.

## Structure & Production Status (reconciled 2026-05-18 for T-29)

| Directory | Status | wrangler `name` | Public route | Description |
|-----------|--------|------|------|------|
| `agent-framework/` | **library** | n/a | n/a | Core `BaseAgent` class — CORS, caching, AI calls, MCP server (JS). Sourced by each production agent via local copy (see T-04). |
| `agent-generator/` | **internal tooling** | `generator` | `generator.aktohcyber.com` | Agent code generation from JSON config (JS, with wrangler deployment support). Not customer-facing. |
| `infosec/` | **production** | `infosec` | `infosec.aktohcyber.com` | Generalist cross-agent coordinator. |
| `judge-js/` | **production** | `judge` | `judge.aktohcyber.com` | Vulnerability / CVE / risk prioritisation. JS variant — this is the one on the production `judge.*` DNS. |
| `lancer/` | **conditional (disabled-by-default)** | `lancer` | `lancer.aktohcyber.com` | Red team / pen-test specialist. Off by default; enable per-customer with consent (see `specs/active/ADR-Lancer-Agent-Status.md`). |
| `scout/` | **production** | `scout` | `scout.aktohcyber.com` | Network reconnaissance / OSINT. |
| `shield/` | **production** | `shield` | `shield.aktohcyber.com` | Blue team / incident response. |
| `cybersec-agent/` | **experimental** | `cybersec-py` | `cybersec.aktohcyber.com` | Python generalist prototype predating the 4-agent split. Retire-candidate — superseded by `infosec/`. |
| `judge/` | **experimental (variant)** | `judge-py` | `judge-py.aktohcyber.com` | Python implementation of judge; runs in parallel with `judge-js` for an A/B comparison of Python-on-Workers vs JS. Document the A/B end date or promote/retire. |
| `tests/` | **shared tests** | n/a | n/a | Pooled Vitest + pytest suites covering the 4 production agents + lancer. |

### Count reconciliation

- `projects/horsemen/CLAUDE.md` and `specs/active/Customer-Readiness-Checklist.md` describe **"5 production agents"**.
- This dir has **8 wrangler-configured agents** + 1 shared library + 1 generator.
- Accurate split: **4 always-on production** (scout, shield, infosec, judge-js) + **1 conditional/opt-in** (lancer) = up to 5 customer-facing agents; **3 are experimental/tooling** (cybersec-agent, judge-py, agent-generator).

### Test policy

- All 4 production agents must keep tests in `tests/` (Vitest for JS, pytest for Py). Today the pool holds 4 JS + 1 Py test file.
- Lancer must keep tests but is excluded from default CI runs, matching its production disable-by-default posture.
- Experimental agents have no test requirement until promoted to production. If `cybersec-agent/` or `judge/` (Python variant) move to production, they get checklist rows + tests at the same time.
- `agent-framework/base-agent.js` is covered transitively when the 4 production agents are tested. A future refactor that imports it directly should add unit tests.

Closes T-29 from `specs/active/Horsemen-Validation-Checklists.md` v2.1.

## How It Works

1. `agent-framework/base-agent.js` provides the foundation: CORS handling, Cloudflare AI calls, MCP protocol support, caching, and conversation memory
2. Each specialist agent extends BaseAgent with domain-specific system prompts, keywords, and patterns
3. `agent-generator/` builds deployable agents from JSON configuration files using templates

## Key Concepts

- **BaseAgent**: Handles HTTP routing, AI model invocation (via Cloudflare Workers AI), and MCP tool exposure
- **RouterAgent**: Extends BaseAgent to route queries to specialist agents using ToolRegistry scoring
- **ToolRegistry**: Dynamic routing with keyword matching (+1 point), regex patterns (+2 points), and priority multipliers
