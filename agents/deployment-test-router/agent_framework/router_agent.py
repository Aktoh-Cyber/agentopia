"""
Router Agent - Extends BaseAgent to route questions to specialized agents
Python implementation for Cloudflare Workers
"""

import json
from typing import Any

# JavaScript console for logging
from js import console

# Import Workers-specific modules
from workers import Response

from .base_agent import BaseAgent
from .tool_registry import DynamicMCPClient, ToolRegistry


class RouterAgent(BaseAgent):
    """Router agent that routes questions to specialized agents"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)

        # Initialize tool registry
        registry_config = config.get("registry", {"tools": []})
        self.registry = ToolRegistry(registry_config)
        self.mcp_client = DynamicMCPClient(self.registry)

    async def process_question(self, env, question: str) -> dict[str, Any]:
        """Override processQuestion to implement routing logic"""
        # Check cache first
        cache_key = f"q:{question.lower().strip()}"
        cached = await self.get_from_cache(env, cache_key)

        if cached:
            return {"answer": cached, "cached": True}

        answer = None
        source = self.config["name"]

        # Try to route to specialized agent
        try:
            tool_result = await self.mcp_client.ask_tool(question)

            if tool_result:
                answer = tool_result["answer"]
                source = tool_result["source"]

                # Add attribution
                answer = f"{answer}\n\n*[This response was provided by {source}]*"

        except Exception as e:
            console.error(f"Failed to contact specialized agent: {e}")
            # Fall through to local AI

        # If no specialized agent or it failed, use local AI
        if not answer:
            # Enhance system prompt with routing awareness
            enhanced_prompt = f"""{self.config['system_prompt']}

Note: You have access to specialized agents for certain topics:
{self.get_tool_summary()}
If a question is better suited for a specialized agent, mention it in your response."""

            # Temporarily update system prompt for this call
            original_prompt = self.config["system_prompt"]
            self.config["system_prompt"] = enhanced_prompt

            answer = await self.call_ai(env, question)

            # Restore original prompt
            self.config["system_prompt"] = original_prompt

        # Cache the response
        await self.put_in_cache(env, cache_key, answer)

        return {"answer": answer, "cached": False, "source": source}

    def get_tool_summary(self) -> str:
        """Get a summary of available tools for the system prompt"""
        tools = self.registry.get_all_tools()
        if not tools:
            return "No specialized agents currently available."

        return "\n".join(f"- {tool['name']}: {tool['description']}" for tool in tools)

    def handle_mcp_tools_list(self) -> dict[str, Any]:
        """Override MCP tools list to include routing capabilities"""
        base_tools = super().handle_mcp_tools_list()

        # Add a tool for listing available agents
        base_tools["tools"].append(
            {
                "name": "list_available_agents",
                "description": "List all available specialized agents",
                "inputSchema": {"type": "object", "properties": {}, "required": []},
            }
        )

        return base_tools

    async def handle_mcp_tool_call(self, env, params: dict[str, Any]) -> dict[str, Any]:
        """Handle additional MCP tool calls"""
        tool_name = params.get("name")

        if tool_name == "list_available_agents":
            tools = self.registry.get_all_tools()
            return {"content": [{"type": "text", "text": json.dumps(tools, indent=2)}]}

        return await super().handle_mcp_tool_call(env, params)

    async def fetch(self, request, env):
        """Add admin endpoint for managing tool registry"""
        from urllib.parse import urlparse

        url = urlparse(request.url)
        method = request.method
        cors_headers = self.get_cors_headers()

        # Admin endpoint to update tool registry
        if method == "POST" and url.path == "/admin/tools":
            try:
                # In production, add authentication here
                request_data = await request.json()
                tool = request_data.get("tool")

                if tool:
                    self.registry.register_tool(tool)

                    # Optionally persist to KV or D1
                    if hasattr(env, "REGISTRY"):
                        registry_json = json.dumps(self.registry.to_dict())
                        await env.REGISTRY.put("tools", registry_json)

                return Response(
                    json.dumps({"success": True, "message": "Tool registered successfully"}),
                    headers={"Content-Type": "application/json", **cors_headers},
                )

            except Exception as e:
                return Response(
                    json.dumps({"success": False, "error": str(e)}),
                    status=400,
                    headers={"Content-Type": "application/json", **cors_headers},
                )

        # Admin endpoint to get current registry
        if method == "GET" and url.path == "/admin/tools":
            return Response(
                json.dumps(self.registry.to_dict()),
                headers={"Content-Type": "application/json", **cors_headers},
            )

        # Delegate to base class for standard endpoints
        return await super().fetch(request, env)


def create_router_agent(config: dict[str, Any]) -> RouterAgent:
    """Factory function to create a router agent from config"""
    return RouterAgent(config)
