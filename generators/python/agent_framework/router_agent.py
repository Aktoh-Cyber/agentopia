"""
Router Agent - Extends BaseAgent to route questions to specialized agents
Now with LangChain-style interface for enhanced routing capabilities
Python implementation for Cloudflare Workers
"""

import json
from typing import Any, List, Optional

# JavaScript console for logging
from js import console

# Import Workers-specific modules
from workers import Response

from .base_agent import BaseAgent, LANGCHAIN_COMPAT_AVAILABLE
from .tool_registry import DynamicMCPClient, ToolRegistry

# Import LangChain-compatible interfaces if available
if LANGCHAIN_COMPAT_AVAILABLE:
    from .langchain_compat import (
        BaseMessage,
        SystemMessage,
        HumanMessage,
        ChatPromptTemplate,
        PromptTemplate,
        BaseChain,
        LLMChain,
        JsonOutputParser,
    )


class RouterChain(BaseChain if LANGCHAIN_COMPAT_AVAILABLE else object):
    """Chain that routes questions to specialized agents"""

    def __init__(self, llm, registry: ToolRegistry, mcp_client: DynamicMCPClient):
        self.llm = llm
        self.registry = registry
        self.mcp_client = mcp_client

        # Create routing analysis prompt
        self.routing_prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are a routing assistant that analyzes questions and determines which specialized agent should handle them.
            
Available specialized agents:
{agents_summary}

Analyze the question and respond with JSON in this format:
{{
    "should_route": true/false,
    "agent_name": "agent name if routing, null otherwise",
    "confidence": 0-100,
    "reasoning": "brief explanation"
}}""",
                ),
                ("human", "{question}"),
            ]
        )

        self.parser = JsonOutputParser()

    async def arun(self, question: str, **kwargs: Any) -> dict[str, Any]:
        """Analyze question and route if appropriate"""
        # Get agents summary
        agents_summary = self._get_agents_summary()

        # Run routing analysis
        analysis = await self.llm.ainvoke(
            self.routing_prompt.format_messages(agents_summary=agents_summary, question=question)
        )

        # Parse result
        try:
            routing_decision = self.parser.parse(analysis)
        except:
            # Fallback to tool registry scoring
            routing_decision = {
                "should_route": False,
                "agent_name": None,
                "confidence": 0,
                "reasoning": "Failed to parse routing decision",
            }

        # If we should route and have high confidence, try the specialized agent
        if routing_decision.get("should_route") and routing_decision.get("confidence", 0) > 70:
            try:
                tool_result = await self.mcp_client.ask_tool(question)
                if tool_result:
                    return {
                        "routed": True,
                        "answer": tool_result["answer"],
                        "source": tool_result["source"],
                        "routing_decision": routing_decision,
                    }
            except Exception as e:
                console.error(f"Failed to contact specialized agent: {e}")

        # Otherwise, use tool registry scoring as fallback
        try:
            tool_result = await self.mcp_client.ask_tool(question)
            if tool_result:
                return {
                    "routed": True,
                    "answer": tool_result["answer"],
                    "source": tool_result["source"],
                    "routing_decision": routing_decision,
                }
        except Exception as e:
            console.error(f"Tool registry routing failed: {e}")

        return {"routed": False, "routing_decision": routing_decision}

    def _get_agents_summary(self) -> str:
        """Get formatted summary of available agents"""
        tools = self.registry.get_all_tools()
        if not tools:
            return "No specialized agents available."

        return "\n".join(
            [
                f"- {tool['name']}: {tool['description']} (keywords: {', '.join(tool.get('keywords', [])[:5])})"
                for tool in tools
            ]
        )


class RouterAgent(BaseAgent):
    """Router agent that routes questions to specialized agents with optional LangChain interface"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)

        # Initialize tool registry
        registry_config = config.get("registry", {"tools": []})
        self.registry = ToolRegistry(registry_config)
        self.mcp_client = DynamicMCPClient(self.registry)

        # Initialize router chain if LangChain is available
        self.router_chain: Optional[RouterChain] = None

    def setup_langchain_components(self, env):
        """Initialize LangChain components with routing chain"""
        super().setup_langchain_components(env)

        if LANGCHAIN_COMPAT_AVAILABLE and self.config["use_langchain"] and self.llm:
            self.router_chain = RouterChain(self.llm, self.registry, self.mcp_client)

    async def process_question_langchain(self, env, question: str) -> dict[str, Any]:
        """Process question using LangChain-style routing"""
        # Initialize components if not already done
        if self.llm is None:
            self.setup_langchain_components(env)

        # Check cache first
        cache_key = f"q:{question.lower().strip()}"
        cached = await self.get_from_cache(env, cache_key)

        if cached:
            return {"answer": cached, "cached": True}

        # Add to memory
        self.memory.add_user_message(question)

        answer = None
        source = self.config["name"]

        # Try routing with LangChain
        if self.router_chain:
            try:
                routing_result = await self.router_chain.arun(question=question)

                if routing_result.get("routed"):
                    answer = routing_result["answer"]
                    source = routing_result["source"]

                    # Add attribution
                    answer = f"{answer}\n\n*[This response was provided by {source}]*"

                    # Log routing decision if available
                    if routing_result.get("routing_decision"):
                        console.log(
                            f"Routing decision: {json.dumps(routing_result['routing_decision'])}"
                        )

            except Exception as e:
                console.error(f"LangChain routing failed: {e}")

        # If no routing or it failed, use local AI with enhanced prompt
        if not answer:
            # Create enhanced prompt with routing awareness
            enhanced_prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        f"""{self.config['system_prompt']}

Note: You have access to specialized agents for certain topics:
{self.get_tool_summary()}
If a question is better suited for a specialized agent, mention it in your response.""",
                    ),
                    ("human", "{question}"),
                ]
            )

            # Run the chain
            answer = await self.chain.llm.ainvoke(
                enhanced_prompt.format_messages(question=question)
            )

            # Parse output
            answer = self.output_parser.parse(answer)

        # Add AI response to memory
        self.memory.add_ai_message(answer)

        # Cache the response
        await self.put_in_cache(env, cache_key, answer)

        return {"answer": answer, "cached": False, "source": source}

    async def process_question_legacy(self, env, question: str) -> dict[str, Any]:
        """Process question using legacy routing (non-LangChain)"""
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

    async def process_question(self, env, question: str) -> dict[str, Any]:
        """Process question using appropriate routing method"""
        if LANGCHAIN_COMPAT_AVAILABLE and self.config["use_langchain"]:
            return await self.process_question_langchain(env, question)
        else:
            return await self.process_question_legacy(env, question)

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
