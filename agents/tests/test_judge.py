"""
Test suite for the Judge agent — Vulnerability & Compliance Expert (Python).

The Judge agent is the only Python-based agent in the Agentopia platform.
It runs on Cloudflare Workers Python runtime (Pyodide) and uses the Python
agent_framework.BaseAgent class.

Since the production code depends on Pyodide-specific FFI imports (js, workers),
these tests mock those dependencies and test the logic in isolation:
  - Route dispatch (GET /, POST /api/ask, POST /mcp, OPTIONS, 404)
  - Response format and content
  - Error handling (missing question, server errors)
  - MCP protocol compliance (tools/list, tools/call)
  - Routing keyword configuration
"""

import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import urlparse


# ─── Mock the Pyodide/Workers imports that base_agent.py needs ───────────

# We cannot import the real base_agent.py because it uses:
#   from js import console
#   from pyodide.ffi import to_js
#   from workers import Response
# So we test the agent logic via a reconstructed stand-in that mirrors the
# actual routing/processing behaviour from the source code.


class MockResponse:
    """Simulates workers.Response for testing."""

    def __init__(self, body="", status=200, headers=None):
        self.body = body
        self.status = status
        self.headers = headers or {}

    def json(self):
        return json.loads(self.body)


class MockRequest:
    """Simulates a Workers request object."""

    def __init__(self, url, method="GET", body=None, headers=None):
        self.url = url
        self.method = method
        self._body = body
        self.headers = headers or {}

    async def json(self):
        if self._body is None:
            raise ValueError("No body")
        if isinstance(self._body, str):
            return json.loads(self._body)
        return self._body


class MockEnv:
    """Simulates the Workers env bindings."""

    def __init__(self, ai_response="Mock AI response", rate_limit_allow=True):
        self.AI = MockAI(ai_response)
        self.CACHE = MockCache()
        self.RATE_LIMITER = MockRateLimiter(rate_limit_allow) if rate_limit_allow is not None else None

    class _NoRateLimiter:
        pass


class MockAI:
    """Simulates env.AI binding."""

    def __init__(self, response_text="Mock AI response"):
        self.response_text = response_text

    async def run(self, model, params):
        return MagicMock(response=self.response_text)


class MockCache:
    """Simulates env.CACHE (KV namespace)."""

    def __init__(self):
        self._store = {}

    async def get(self, key):
        return self._store.get(key)

    async def put(self, key, value, **kwargs):
        self._store[key] = value


class MockRateLimiter:
    """Simulates env.RATE_LIMITER."""

    def __init__(self, allow=True):
        self._allow = allow

    async def limit(self, key=None):
        return MagicMock(success=self._allow)


# ─── Judge agent logic (reconstructed from source for testability) ────────

JUDGE_CONFIG = {
    "type": "specialist",
    "name": "Judge - Vulnerability & Compliance Expert",
    "description": "Specialized Python AI for vulnerability assessment and compliance frameworks",
    "icon": "\u2696\ufe0f",
    "systemPrompt": (
        "You are a specialized cybersecurity expert focused on vulnerability "
        "assessment and compliance."
    ),
    "examples": [
        "What is CVE-2021-44228 (Log4Shell) and how do I remediate it?",
        "What are the key requirements for SOC 2 Type II compliance?",
    ],
    "aiLabel": "Judge",
    "model": "@cf/meta/llama-3.1-8b-instruct",
    "maxTokens": 512,
    "temperature": 0.3,
    "cacheEnabled": False,  # Disable caching in tests for simplicity
    "cacheTTL": 3600,
    "mcpToolName": "judge_vulnerability_compliance",
    "keywords": [
        "cve", "vulnerability", "vulnerabilities", "exploit", "patch",
        "cvss", "score", "severity", "critical", "high risk",
        "compliance", "compliant", "regulation", "framework",
        "soc 2", "soc2", "iso 27001", "iso27001", "nist", "gdpr",
        "hipaa", "pci-dss", "pci dss", "pcidss",
    ],
    "patterns": [r"CVE-\d{4}-\d+", r"\b(SOC\s*2|GDPR|HIPAA|PCI[- ]?DSS)\b"],
    "priority": 10,
}


class JudgeAgent:
    """
    Reconstructed Judge agent for testing.
    Mirrors the logic in agents/judge/agent_framework/base_agent.py
    and agents/judge/src/entry.py.
    """

    def __init__(self, config):
        self.config = config

    def get_cors_headers(self):
        return {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type",
        }

    async def process_question(self, env, question):
        ai_result = await env.AI.run(
            self.config["model"],
            {
                "messages": [
                    {"role": "system", "content": self.config["systemPrompt"]},
                    {"role": "user", "content": f"Question: {question}"},
                ],
            },
        )
        answer = ai_result.response or "I apologize, but I could not generate a response."
        return {"answer": answer, "cached": False}

    def handle_mcp_tools_list(self):
        return {
            "tools": [
                {
                    "name": self.config["mcpToolName"],
                    "description": self.config["description"],
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "question": {
                                "type": "string",
                                "description": "Question to ask the agent",
                            }
                        },
                        "required": ["question"],
                    },
                }
            ]
        }

    async def handle_mcp_tool_call(self, env, params):
        question = params.get("arguments", {}).get("question")
        if not question:
            return {
                "error": {"code": -32602, "message": "Invalid params: question is required"}
            }
        result = await self.process_question(env, question)
        return {"content": [{"type": "text", "text": result["answer"]}]}

    async def handle_mcp_request(self, env, request_data):
        method = request_data.get("method")
        if method == "tools/list":
            return self.handle_mcp_tools_list()
        if method == "tools/call":
            tool_name = request_data.get("params", {}).get("name")
            if tool_name == self.config["mcpToolName"]:
                return await self.handle_mcp_tool_call(env, request_data.get("params", {}))
        return {"error": {"code": -32601, "message": "Method not found"}}

    async def fetch(self, request, env):
        url = urlparse(request.url)
        method = request.method
        cors = self.get_cors_headers()

        if method == "OPTIONS":
            return MockResponse("", 200, cors)

        if method == "GET" and url.path == "/":
            return MockResponse(
                f"<html>{self.config['name']}</html>",
                200,
                {"Content-Type": "text/html", **cors},
            )

        if method == "POST" and url.path == "/mcp":
            try:
                request_data = await request.json()
                result = await self.handle_mcp_request(env, request_data)
                return MockResponse(
                    json.dumps(result),
                    200,
                    {"Content-Type": "application/json", **cors},
                )
            except Exception:
                return MockResponse(
                    json.dumps({"error": {"code": -32603, "message": "Internal error"}}),
                    500,
                    {"Content-Type": "application/json", **cors},
                )

        if method == "POST" and url.path == "/api/ask":
            try:
                request_data = await request.json()
                question = request_data.get("question", "").strip()
                if not question:
                    return MockResponse(
                        json.dumps({"error": "Question is required"}),
                        400,
                        {"Content-Type": "application/json", **cors},
                    )
                result = await self.process_question(env, question)
                return MockResponse(
                    json.dumps(result),
                    200,
                    {"Content-Type": "application/json", **cors},
                )
            except Exception:
                return MockResponse(
                    json.dumps({"error": "An error occurred processing your request"}),
                    500,
                    {"Content-Type": "application/json", **cors},
                )

        return MockResponse("Not Found", 404)


async def fetch_with_rate_limit(agent, request, env):
    """Wraps agent.fetch with rate-limit logic matching entry.py."""
    if hasattr(env, "RATE_LIMITER") and env.RATE_LIMITER is not None:
        client_ip = request.headers.get("cf-connecting-ip", "unknown")
        result = await env.RATE_LIMITER.limit(key=client_ip)
        if not result.success:
            return MockResponse(
                '{"error": "Rate limit exceeded. Please try again later."}',
                429,
                {"Content-Type": "application/json", "Retry-After": "60"},
            )
    return await agent.fetch(request, env)


# ─── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def agent():
    return JudgeAgent(JUDGE_CONFIG)


@pytest.fixture
def env():
    return MockEnv()


# ─── Tests ────────────────────────────────────────────────────────────────


class TestRouteDispatch:
    @pytest.mark.asyncio
    async def test_get_homepage(self, agent, env):
        req = MockRequest("https://judge-py.mindhive.tech/", "GET")
        res = await fetch_with_rate_limit(agent, req, env)
        assert res.status == 200
        assert "text/html" in res.headers.get("Content-Type", "")
        assert "Judge" in res.body

    @pytest.mark.asyncio
    async def test_options_returns_cors(self, agent, env):
        req = MockRequest("https://judge-py.mindhive.tech/api/ask", "OPTIONS")
        res = await fetch_with_rate_limit(agent, req, env)
        assert res.status == 200
        assert res.headers.get("Access-Control-Allow-Origin") == "*"

    @pytest.mark.asyncio
    async def test_unknown_route_returns_404(self, agent, env):
        req = MockRequest("https://judge-py.mindhive.tech/unknown", "GET")
        res = await fetch_with_rate_limit(agent, req, env)
        assert res.status == 404

    @pytest.mark.asyncio
    async def test_get_api_ask_returns_404(self, agent, env):
        req = MockRequest("https://judge-py.mindhive.tech/api/ask", "GET")
        res = await fetch_with_rate_limit(agent, req, env)
        assert res.status == 404


class TestPostApiAsk:
    @pytest.mark.asyncio
    async def test_valid_question_returns_answer(self, agent, env):
        env.AI = MockAI("Log4Shell is a critical RCE vulnerability")
        req = MockRequest(
            "https://judge-py.mindhive.tech/api/ask",
            "POST",
            body={"question": "What is CVE-2021-44228?"},
        )
        res = await fetch_with_rate_limit(agent, req, env)
        assert res.status == 200
        data = res.json()
        assert "answer" in data
        assert data["answer"] == "Log4Shell is a critical RCE vulnerability"
        assert data["cached"] is False

    @pytest.mark.asyncio
    async def test_empty_question_returns_400(self, agent, env):
        req = MockRequest(
            "https://judge-py.mindhive.tech/api/ask",
            "POST",
            body={"question": ""},
        )
        res = await fetch_with_rate_limit(agent, req, env)
        assert res.status == 400
        data = res.json()
        assert "error" in data
        assert "required" in data["error"].lower()

    @pytest.mark.asyncio
    async def test_whitespace_question_returns_400(self, agent, env):
        req = MockRequest(
            "https://judge-py.mindhive.tech/api/ask",
            "POST",
            body={"question": "   "},
        )
        res = await fetch_with_rate_limit(agent, req, env)
        assert res.status == 400

    @pytest.mark.asyncio
    async def test_ai_failure_returns_500(self, agent, env):
        env.AI = MagicMock()
        env.AI.run = AsyncMock(side_effect=Exception("AI down"))
        req = MockRequest(
            "https://judge-py.mindhive.tech/api/ask",
            "POST",
            body={"question": "test"},
        )
        res = await fetch_with_rate_limit(agent, req, env)
        assert res.status == 500

    @pytest.mark.asyncio
    async def test_response_includes_cors_headers(self, agent, env):
        req = MockRequest(
            "https://judge-py.mindhive.tech/api/ask",
            "POST",
            body={"question": "test"},
        )
        res = await fetch_with_rate_limit(agent, req, env)
        assert res.headers.get("Access-Control-Allow-Origin") == "*"

    @pytest.mark.asyncio
    async def test_response_content_type_is_json(self, agent, env):
        req = MockRequest(
            "https://judge-py.mindhive.tech/api/ask",
            "POST",
            body={"question": "test"},
        )
        res = await fetch_with_rate_limit(agent, req, env)
        assert res.headers.get("Content-Type") == "application/json"


class TestRateLimiting:
    @pytest.mark.asyncio
    async def test_rate_limit_exceeded_returns_429(self, agent):
        env = MockEnv(rate_limit_allow=False)
        req = MockRequest(
            "https://judge-py.mindhive.tech/api/ask",
            "POST",
            body={"question": "test"},
        )
        res = await fetch_with_rate_limit(agent, req, env)
        assert res.status == 429
        data = res.json()
        assert "rate limit" in data["error"].lower()
        assert res.headers.get("Retry-After") == "60"

    @pytest.mark.asyncio
    async def test_rate_limit_allowed_passes_through(self, agent, env):
        req = MockRequest(
            "https://judge-py.mindhive.tech/api/ask",
            "POST",
            body={"question": "test"},
        )
        res = await fetch_with_rate_limit(agent, req, env)
        assert res.status == 200


class TestMCPProtocol:
    @pytest.mark.asyncio
    async def test_tools_list_returns_judge_tool(self, agent, env):
        req = MockRequest(
            "https://judge-py.mindhive.tech/mcp",
            "POST",
            body={"method": "tools/list"},
        )
        res = await fetch_with_rate_limit(agent, req, env)
        assert res.status == 200
        data = res.json()
        assert "tools" in data
        assert len(data["tools"]) == 1
        tool = data["tools"][0]
        assert tool["name"] == "judge_vulnerability_compliance"
        assert "inputSchema" in tool
        assert "question" in tool["inputSchema"]["required"]

    @pytest.mark.asyncio
    async def test_tools_call_with_question(self, agent, env):
        env.AI = MockAI("CVSS 10.0 critical")
        req = MockRequest(
            "https://judge-py.mindhive.tech/mcp",
            "POST",
            body={
                "method": "tools/call",
                "params": {
                    "name": "judge_vulnerability_compliance",
                    "arguments": {"question": "What is the CVSS score of Log4Shell?"},
                },
            },
        )
        res = await fetch_with_rate_limit(agent, req, env)
        assert res.status == 200
        data = res.json()
        assert data["content"][0]["type"] == "text"
        assert data["content"][0]["text"] == "CVSS 10.0 critical"

    @pytest.mark.asyncio
    async def test_tools_call_missing_question_returns_error(self, agent, env):
        req = MockRequest(
            "https://judge-py.mindhive.tech/mcp",
            "POST",
            body={
                "method": "tools/call",
                "params": {
                    "name": "judge_vulnerability_compliance",
                    "arguments": {},
                },
            },
        )
        res = await fetch_with_rate_limit(agent, req, env)
        data = res.json()
        assert data["error"]["code"] == -32602

    @pytest.mark.asyncio
    async def test_unknown_mcp_method_returns_error(self, agent, env):
        req = MockRequest(
            "https://judge-py.mindhive.tech/mcp",
            "POST",
            body={"method": "resources/list"},
        )
        res = await fetch_with_rate_limit(agent, req, env)
        data = res.json()
        assert data["error"]["code"] == -32601

    @pytest.mark.asyncio
    async def test_wrong_tool_name_returns_method_not_found(self, agent, env):
        req = MockRequest(
            "https://judge-py.mindhive.tech/mcp",
            "POST",
            body={
                "method": "tools/call",
                "params": {
                    "name": "wrong_tool_name",
                    "arguments": {"question": "test"},
                },
            },
        )
        res = await fetch_with_rate_limit(agent, req, env)
        data = res.json()
        assert data["error"]["code"] == -32601


class TestJudgeConfig:
    """Verify the Judge agent configuration is correct."""

    def test_mcp_tool_name(self):
        assert JUDGE_CONFIG["mcpToolName"] == "judge_vulnerability_compliance"

    def test_model_configured(self):
        assert JUDGE_CONFIG["model"] == "@cf/meta/llama-3.1-8b-instruct"

    def test_has_vulnerability_keywords(self):
        keywords = JUDGE_CONFIG["keywords"]
        assert "cve" in keywords
        assert "vulnerability" in keywords
        assert "compliance" in keywords
        assert "gdpr" in keywords

    def test_has_cve_pattern(self):
        import re
        patterns = JUDGE_CONFIG["patterns"]
        cve_pattern = patterns[0]
        assert re.search(cve_pattern, "CVE-2021-44228")
        assert not re.search(cve_pattern, "not a CVE")

    def test_has_framework_pattern(self):
        import re
        patterns = JUDGE_CONFIG["patterns"]
        fw_pattern = patterns[1]
        assert re.search(fw_pattern, "SOC 2 compliance")
        assert re.search(fw_pattern, "GDPR requirements")
        assert re.search(fw_pattern, "HIPAA regulations")
        assert re.search(fw_pattern, "PCI-DSS")

    def test_priority(self):
        assert JUDGE_CONFIG["priority"] == 10

    def test_temperature_is_low(self):
        # Security agents should use low temperature for factual responses
        assert JUDGE_CONFIG["temperature"] <= 0.5
