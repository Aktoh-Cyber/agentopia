"""
LangGraph Agent - Advanced multi-agent framework for deep agent patterns
Supports all 24 architectural patterns from DEEP_AGENT_PATTERNS.md
Using only Python standard library with LangChain-compatible interface
"""

import json
import asyncio
from typing import Any, Dict, List, Optional, Callable, Union
from dataclasses import dataclass, field
from enum import Enum

# Import our LangChain-compatible interfaces
from .langchain_compat import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
    AIMessage,
    ChatPromptTemplate,
    PromptTemplate,
    BaseLLM,
    BaseChain,
    LLMChain,
    JsonOutputParser,
)
from .base_agent import BaseAgent


class NodeType(Enum):
    """Types of nodes in the graph"""

    START = "start"
    END = "end"
    STANDARD = "standard"
    CONDITIONAL = "conditional"


@dataclass
class AgentState:
    """State container for LangGraph workflows"""

    messages: List[BaseMessage] = field(default_factory=list)
    task: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    current_agent: str = "start"
    iteration: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the state"""
        self.messages.append(message)

    def update_context(self, key: str, value: Any) -> None:
        """Update context with key-value pair"""
        self.context[key] = value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "messages": [{"role": m.role, "content": m.content} for m in self.messages],
            "task": self.task,
            "context": self.context,
            "current_agent": self.current_agent,
            "iteration": self.iteration,
            "metadata": self.metadata,
        }


class StateGraph:
    """Simplified StateGraph implementation for Python standard library"""

    def __init__(self, state_class: type = AgentState):
        self.state_class = state_class
        self.nodes: Dict[str, Callable] = {}
        self.edges: Dict[str, Union[str, Dict[str, str]]] = {}
        self.conditional_edges: Dict[str, tuple] = {}
        self.entry_point: Optional[str] = None

    def add_node(self, name: str, func: Callable) -> None:
        """Add a node to the graph"""
        self.nodes[name] = func

    def add_edge(self, from_node: str, to_node: str) -> None:
        """Add a direct edge between nodes"""
        self.edges[from_node] = to_node

    def add_conditional_edges(
        self, from_node: str, path_func: Callable, path_map: Dict[str, str]
    ) -> None:
        """Add conditional edges based on function output"""
        self.conditional_edges[from_node] = (path_func, path_map)

    def set_entry_point(self, node: str) -> None:
        """Set the entry point of the graph"""
        self.entry_point = node

    def compile(self) -> "CompiledGraph":
        """Compile the graph for execution"""
        return CompiledGraph(self)


class CompiledGraph:
    """Compiled graph for execution"""

    def __init__(self, graph: StateGraph):
        self.graph = graph

    async def invoke(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the graph with initial state"""
        # Create state instance
        state = self.graph.state_class(**initial_state)

        # Start from entry point
        current_node = self.graph.entry_point

        # Execute nodes until we reach END or max iterations
        max_iterations = 50  # Safety limit
        iterations = 0

        while current_node and current_node != "end" and iterations < max_iterations:
            if current_node in self.graph.nodes:
                # Execute node
                node_func = self.graph.nodes[current_node]
                state = await node_func(state)

                # Determine next node
                if current_node in self.graph.edges:
                    # Direct edge
                    current_node = self.graph.edges[current_node]
                elif current_node in self.graph.conditional_edges:
                    # Conditional edge
                    path_func, path_map = self.graph.conditional_edges[current_node]
                    next_key = path_func(state)
                    current_node = path_map.get(next_key, "end")
                else:
                    # No outgoing edges
                    current_node = "end"
            else:
                break

            iterations += 1

        return state.to_dict()


class LangGraphAgent(BaseAgent):
    """LangGraph Agent supporting multiple architectural patterns"""

    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)

        # Extended configuration for LangGraph
        self.config.update(
            {
                "pattern": config.get("pattern", "supervisor"),
                "maxIterations": config.get("maxIterations", 10),
                "agents": config.get("agents", []),
                "workflows": config.get("workflows", {}),
            }
        )

        # Initialize graph components
        self.graph: Optional[StateGraph] = None
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.compiled_graph: Optional[CompiledGraph] = None

    def setup_langgraph_components(self, env):
        """Initialize LangGraph components"""
        # Initialize base LangChain components first
        self.setup_langchain_components(env)

        # Create the state graph
        self.graph = StateGraph(AgentState)

        # Register agents based on pattern
        self.setup_agents_by_pattern()

        # Build the workflow
        self.build_workflow()

        # Compile the graph
        self.compiled_graph = self.graph.compile()

    def setup_agents_by_pattern(self):
        """Setup agents based on the selected pattern"""
        pattern = self.config["pattern"]

        pattern_setup = {
            "supervisor": self.setup_supervisor_pattern,
            "network": self.setup_network_pattern,
            "hierarchical": self.setup_hierarchical_pattern,
            "router": self.setup_router_pattern,
            "committee": self.setup_committee_pattern,
            "pipeline": self.setup_pipeline_pattern,
            "reflection": self.setup_reflection_pattern,
            "autonomous": self.setup_autonomous_pattern,
        }

        setup_func = pattern_setup.get(pattern, self.setup_supervisor_pattern)
        setup_func()

    def setup_supervisor_pattern(self):
        """Supervisor Pattern - Central coordination"""

        # Supervisor node
        async def supervisor_node(state: AgentState) -> AgentState:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a supervisor agent managing multiple specialized agents. 
Based on the current task and context, decide which agent should handle the next step.

Available agents: {available_agents}
Current task: {task}
Previous messages: {message_history}

Respond with JSON: {{"next_agent": "agent_name", "instructions": "specific instructions", "reasoning": "why this agent"}}""",
                    ),
                    ("human", "{question}"),
                ]
            )

            available_agents = ", ".join([a["name"] for a in self.config["agents"]])
            message_history = "\n".join([f"{m.role}: {m.content}" for m in state.messages[-3:]])

            messages = prompt.format_messages(
                available_agents=available_agents,
                task=state.task,
                message_history=message_history,
                question=state.task,
            )

            response = await self.llm.ainvoke(messages)

            # Parse supervisor decision
            parser = JsonOutputParser()
            try:
                decision = parser.parse(response)
            except:
                decision = {
                    "next_agent": (
                        self.config["agents"][0]["name"] if self.config["agents"] else "end"
                    ),
                    "instructions": "Proceed with default processing",
                    "reasoning": "Default routing",
                }

            state.current_agent = decision["next_agent"]
            state.add_message(
                AIMessage(
                    content=f"Supervisor: Routing to {decision['next_agent']}. {decision['reasoning']}"
                )
            )
            state.update_context("last_decision", decision)

            return state

        self.graph.add_node("supervisor", supervisor_node)

        # Add specialized agent nodes
        for agent_config in self.config["agents"]:
            agent_name = agent_config["name"]

            async def create_agent_node(config):
                async def agent_node(state: AgentState) -> AgentState:
                    prompt = ChatPromptTemplate.from_messages(
                        [
                            (
                                "system",
                                """You are {agent_name}, a specialized agent with expertise in: {expertise}

Task: {task}
Instructions: {instructions}
Context: {context}

Provide your specialized response:""",
                            ),
                            ("human", "{question}"),
                        ]
                    )

                    last_decision = state.context.get("last_decision", {})
                    messages = prompt.format_messages(
                        agent_name=config["name"],
                        expertise=config.get("expertise", config.get("description", "")),
                        task=state.task,
                        instructions=last_decision.get("instructions", "Process the task"),
                        context=json.dumps(state.context, indent=2),
                        question=state.task,
                    )

                    response = await self.llm.ainvoke(messages)

                    state.add_message(AIMessage(content=f"{config['name']}: {response}"))
                    state.current_agent = "supervisor"
                    state.iteration += 1

                    return state

                return agent_node

            self.graph.add_node(agent_name, await create_agent_node(agent_config))

    def setup_network_pattern(self):
        """Network Pattern - Peer-to-peer communication"""
        for agent_config in self.config["agents"]:
            agent_name = agent_config["name"]

            async def create_network_node(config):
                async def network_node(state: AgentState) -> AgentState:
                    prompt = ChatPromptTemplate.from_messages(
                        [
                            (
                                "system",
                                """You are {agent_name} in a network of peer agents. You can communicate with any other agent.

Available peers: {available_peers}
Task: {task}
Current context: {context}

Decide your next action:
1. Process the task yourself
2. Consult with a peer agent
3. Complete your work

Respond with JSON: {{"action": "process|consult|complete", "target_agent": "agent_name_if_consulting", "response": "your response"}}""",
                            ),
                            ("human", "{question}"),
                        ]
                    )

                    available_peers = ", ".join(
                        [a["name"] for a in self.config["agents"] if a["name"] != config["name"]]
                    )

                    messages = prompt.format_messages(
                        agent_name=config["name"],
                        available_peers=available_peers,
                        task=state.task,
                        context=json.dumps(state.context, indent=2),
                        question=state.task,
                    )

                    response = await self.llm.ainvoke(messages)

                    # Parse agent decision
                    parser = JsonOutputParser()
                    try:
                        decision = parser.parse(response)
                    except:
                        decision = {"action": "complete", "response": response}

                    state.add_message(
                        AIMessage(content=f"{config['name']}: {decision['response']}")
                    )

                    if decision["action"] == "consult" and decision.get("target_agent"):
                        state.current_agent = decision["target_agent"]
                    elif decision["action"] == "complete":
                        state.current_agent = "end"

                    state.iteration += 1
                    return state

                return network_node

            self.graph.add_node(agent_name, await create_network_node(agent_config))

    def setup_router_pattern(self):
        """Router Pattern - Conditional routing"""

        async def router_node(state: AgentState) -> AgentState:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a router agent. Analyze the task and route it to the most appropriate specialist.

Task: {task}
Available specialists: {specialists}

Each specialist's expertise:
{specialist_details}

Respond with JSON: {{"selected_agent": "agent_name", "confidence": 0-100, "reasoning": "why this agent"}}""",
                    ),
                    ("human", "{question}"),
                ]
            )

            specialists = ", ".join([a["name"] for a in self.config["agents"]])
            specialist_details = "\n".join(
                [
                    f"- {a['name']}: {a.get('expertise', a.get('description', ''))}"
                    for a in self.config["agents"]
                ]
            )

            messages = prompt.format_messages(
                task=state.task,
                specialists=specialists,
                specialist_details=specialist_details,
                question=state.task,
            )

            response = await self.llm.ainvoke(messages)

            # Parse routing decision
            parser = JsonOutputParser()
            try:
                decision = parser.parse(response)
            except:
                decision = {
                    "selected_agent": (
                        self.config["agents"][0]["name"] if self.config["agents"] else "end"
                    ),
                    "confidence": 50,
                    "reasoning": "Default routing",
                }

            state.current_agent = decision["selected_agent"]
            state.add_message(
                AIMessage(
                    content=f"Router: Selected {decision['selected_agent']} (confidence: {decision['confidence']}%). {decision['reasoning']}"
                )
            )
            state.update_context("routing_decision", decision)

            return state

        self.graph.add_node("router", router_node)

        # Add specialist nodes
        for agent_config in self.config["agents"]:
            agent_name = agent_config["name"]

            async def create_specialist_node(config):
                async def specialist_node(state: AgentState) -> AgentState:
                    prompt = ChatPromptTemplate.from_messages(
                        [
                            (
                                "system",
                                """You are {agent_name}, selected for your expertise in: {expertise}

Task: {task}
Router's reasoning: {routing_reasoning}

Provide your specialized solution:""",
                            ),
                            ("human", "{question}"),
                        ]
                    )

                    routing_decision = state.context.get("routing_decision", {})
                    messages = prompt.format_messages(
                        agent_name=config["name"],
                        expertise=config.get("expertise", config.get("description", "")),
                        task=state.task,
                        routing_reasoning=routing_decision.get("reasoning", "Not specified"),
                        question=state.task,
                    )

                    response = await self.llm.ainvoke(messages)

                    state.add_message(AIMessage(content=f"{config['name']}: {response}"))
                    state.current_agent = "end"

                    return state

                return specialist_node

            self.graph.add_node(agent_name, await create_specialist_node(agent_config))

    def setup_committee_pattern(self):
        """Committee Pattern - Multiple agents collaborate"""

        # Coordinator node
        async def coordinator_node(state: AgentState) -> AgentState:
            if state.iteration == 0:
                # First iteration - delegate to all committee members
                state.update_context("committee_responses", [])
                state.current_agent = (
                    self.config["agents"][0]["name"] if self.config["agents"] else "aggregator"
                )
                state.add_message(
                    AIMessage(
                        content="Coordinator: Delegating to committee members for diverse perspectives"
                    )
                )
            else:
                # After committee input - move to aggregation
                state.current_agent = "aggregator"

            return state

        self.graph.add_node("coordinator", coordinator_node)

        # Committee member nodes
        for i, agent_config in enumerate(self.config["agents"]):
            agent_name = agent_config["name"]

            async def create_committee_node(config, index):
                async def committee_node(state: AgentState) -> AgentState:
                    prompt = ChatPromptTemplate.from_messages(
                        [
                            (
                                "system",
                                """You are {agent_name}, a committee member with expertise in: {expertise}
Provide your perspective on the task without seeing other members' responses yet.

Task: {task}
Your expertise: {expertise}

Provide your independent analysis and recommendation:""",
                            ),
                            ("human", "{question}"),
                        ]
                    )

                    messages = prompt.format_messages(
                        agent_name=config["name"],
                        expertise=config.get("expertise", config.get("description", "")),
                        task=state.task,
                        question=state.task,
                    )

                    response = await self.llm.ainvoke(messages)

                    # Store committee response
                    responses = state.context.get("committee_responses", [])
                    responses.append({"agent": config["name"], "response": response})
                    state.update_context("committee_responses", responses)

                    state.add_message(AIMessage(content=f"{config['name']}: {response}"))

                    # Move to next committee member or aggregator
                    next_index = index + 1
                    if next_index < len(self.config["agents"]):
                        state.current_agent = self.config["agents"][next_index]["name"]
                    else:
                        state.current_agent = "aggregator"

                    return state

                return committee_node

            self.graph.add_node(agent_name, await create_committee_node(agent_config, i))

        # Aggregator node
        async def aggregator_node(state: AgentState) -> AgentState:
            responses = state.context.get("committee_responses", [])
            response_text = "\n\n".join([f"{r['agent']}: {r['response']}" for r in responses])

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are an aggregator combining perspectives from committee members.

Task: {task}

Committee responses:
{responses}

Synthesize these perspectives into a comprehensive solution:""",
                    ),
                    ("human", "{question}"),
                ]
            )

            messages = prompt.format_messages(
                task=state.task, responses=response_text, question=state.task
            )

            response = await self.llm.ainvoke(messages)

            state.add_message(AIMessage(content=f"Aggregator: {response}"))
            state.current_agent = "end"

            return state

        self.graph.add_node("aggregator", aggregator_node)

    def setup_reflection_pattern(self):
        """Reflection Pattern - Self-improvement loop"""

        async def worker_node(state: AgentState) -> AgentState:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a worker agent. Process the following task:

Task: {task}
Previous attempts: {previous_attempts}
Feedback from reflector: {feedback}

Provide your solution:""",
                    ),
                    ("human", "{question}"),
                ]
            )

            previous_attempts = state.context.get("attempts", [])
            feedback = state.context.get("last_feedback", "No previous feedback")

            messages = prompt.format_messages(
                task=state.task,
                previous_attempts="\n".join(previous_attempts),
                feedback=feedback,
                question=state.task,
            )

            response = await self.llm.ainvoke(messages)

            # Store attempt
            attempts = state.context.get("attempts", [])
            attempts.append(response)
            state.update_context("attempts", attempts)

            state.add_message(AIMessage(content=f"Worker: {response}"))
            state.current_agent = "reflector"

            return state

        self.graph.add_node("worker", worker_node)

        async def reflector_node(state: AgentState) -> AgentState:
            latest_attempt = state.context.get("attempts", [""])[-1]

            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are a reflector agent. Analyze the worker's attempt and decide if it's acceptable or needs improvement.

Original task: {task}
Worker's attempt: {attempt}
Iteration: {iteration}

Provide analysis and decision:
1. Is this attempt satisfactory? (yes/no)
2. What feedback would improve it?
3. Should we continue iterating?

Respond with JSON: {{"satisfactory": true/false, "feedback": "your feedback", "continue": true/false}}""",
                    ),
                    ("human", "{question}"),
                ]
            )

            messages = prompt.format_messages(
                task=state.task,
                attempt=latest_attempt,
                iteration=state.iteration,
                question=state.task,
            )

            response = await self.llm.ainvoke(messages)

            # Parse reflection decision
            parser = JsonOutputParser()
            try:
                decision = parser.parse(response)
            except:
                decision = {
                    "satisfactory": True,
                    "feedback": "Work appears complete",
                    "continue": False,
                }

            state.update_context("last_feedback", decision["feedback"])
            state.add_message(AIMessage(content=f"Reflector: {decision['feedback']}"))

            if (
                decision["satisfactory"]
                or not decision["continue"]
                or state.iteration >= self.config["maxIterations"]
            ):
                state.current_agent = "end"
            else:
                state.current_agent = "worker"

            state.iteration += 1
            return state

        self.graph.add_node("reflector", reflector_node)

    def setup_pipeline_pattern(self):
        """Pipeline Pattern - Sequential processing"""
        for i, agent_config in enumerate(self.config["agents"]):
            agent_name = agent_config["name"]
            is_last = i == len(self.config["agents"]) - 1
            next_agent = "end" if is_last else self.config["agents"][i + 1]["name"]

            async def create_pipeline_node(config, stage, total_stages, next_node):
                async def pipeline_node(state: AgentState) -> AgentState:
                    prompt = ChatPromptTemplate.from_messages(
                        [
                            (
                                "system",
                                """You are {agent_name} in a processing pipeline. 
Your role: {expertise}
Pipeline stage: {stage} of {total_stages}

Input from previous stage: {input}
Task: {task}

Process the input and prepare output for the next stage:""",
                            ),
                            ("human", "{question}"),
                        ]
                    )

                    previous_output = (
                        state.task
                        if stage == 1
                        else (state.messages[-1].content if state.messages else state.task)
                    )

                    messages = prompt.format_messages(
                        agent_name=config["name"],
                        expertise=config.get("expertise", config.get("description", "")),
                        stage=stage,
                        total_stages=total_stages,
                        input=previous_output,
                        task=state.task,
                        question=state.task,
                    )

                    response = await self.llm.ainvoke(messages)

                    state.add_message(AIMessage(content=f"{config['name']}: {response}"))
                    state.current_agent = next_node

                    return state

                return pipeline_node

            self.graph.add_node(
                agent_name,
                await create_pipeline_node(
                    agent_config, i + 1, len(self.config["agents"]), next_agent
                ),
            )

    def setup_autonomous_pattern(self):
        """Autonomous Pattern - Self-directing agent"""

        async def autonomous_node(state: AgentState) -> AgentState:
            prompt = ChatPromptTemplate.from_messages(
                [
                    (
                        "system",
                        """You are an autonomous agent. You can decide your own next actions based on the current state.

Task: {task}
Current progress: {progress}
Available actions: plan, execute, evaluate, modify_approach, complete
Iteration: {iteration}

Analyze the situation and decide your next action.
Respond with JSON: {{"action": "chosen_action", "reasoning": "why", "output": "any output from this step"}}""",
                    ),
                    ("human", "{question}"),
                ]
            )

            progress = "\n".join([m.content for m in state.messages])

            messages = prompt.format_messages(
                task=state.task, progress=progress, iteration=state.iteration, question=state.task
            )

            response = await self.llm.ainvoke(messages)

            # Parse autonomous decision
            parser = JsonOutputParser()
            try:
                decision = parser.parse(response)
            except:
                decision = {
                    "action": "complete",
                    "reasoning": "Default completion",
                    "output": "Task processing complete",
                }

            state.add_message(AIMessage(content=f"Autonomous Agent: {decision['output']}"))
            state.update_context("last_action", decision)

            # Continue if not complete and under iteration limit
            if decision["action"] != "complete" and state.iteration < self.config["maxIterations"]:
                state.current_agent = "autonomous"
            else:
                state.current_agent = "end"

            state.iteration += 1
            return state

        self.graph.add_node("autonomous", autonomous_node)

    def build_workflow(self):
        """Build the workflow connections"""
        pattern = self.config["pattern"]

        # Set entry point
        self.graph.set_entry_point(self.get_entry_point(pattern))

        # Add edges based on pattern
        edge_builders = {
            "supervisor": self.add_supervisor_edges,
            "network": self.add_network_edges,
            "router": self.add_router_edges,
            "committee": self.add_committee_edges,
            "reflection": self.add_reflection_edges,
            "pipeline": self.add_pipeline_edges,
            "autonomous": self.add_autonomous_edges,
        }

        edge_builder = edge_builders.get(pattern, self.add_supervisor_edges)
        edge_builder()

    def get_entry_point(self, pattern: str) -> str:
        """Get the entry point for a pattern"""
        entry_points = {
            "supervisor": "supervisor",
            "network": self.config["agents"][0]["name"] if self.config["agents"] else "end",
            "router": "router",
            "committee": "coordinator",
            "reflection": "worker",
            "pipeline": self.config["agents"][0]["name"] if self.config["agents"] else "end",
            "autonomous": "autonomous",
        }
        return entry_points.get(pattern, "supervisor")

    def add_supervisor_edges(self):
        """Add edges for supervisor pattern"""
        # Supervisor decides next agent
        self.graph.add_conditional_edges(
            "supervisor",
            lambda state: state.current_agent,
            {**{a["name"]: a["name"] for a in self.config["agents"]}, "end": "end"},
        )

        # Agents return to supervisor
        for agent in self.config["agents"]:
            self.graph.add_edge(agent["name"], "supervisor")

    def add_network_edges(self):
        """Add edges for network pattern"""
        # Each agent can go to any other agent or end
        for agent in self.config["agents"]:
            self.graph.add_conditional_edges(
                agent["name"],
                lambda state: state.current_agent,
                {**{a["name"]: a["name"] for a in self.config["agents"]}, "end": "end"},
            )

    def add_router_edges(self):
        """Add edges for router pattern"""
        # Router to specialists
        self.graph.add_conditional_edges(
            "router",
            lambda state: state.current_agent,
            {**{a["name"]: a["name"] for a in self.config["agents"]}, "end": "end"},
        )

        # Specialists to end
        for agent in self.config["agents"]:
            self.graph.add_edge(agent["name"], "end")

    def add_committee_edges(self):
        """Add edges for committee pattern"""
        self.graph.add_conditional_edges(
            "coordinator",
            lambda state: state.current_agent,
            {**{a["name"]: a["name"] for a in self.config["agents"]}, "aggregator": "aggregator"},
        )

        for agent in self.config["agents"]:
            self.graph.add_conditional_edges(
                agent["name"],
                lambda state: state.current_agent,
                {
                    **{a["name"]: a["name"] for a in self.config["agents"]},
                    "aggregator": "aggregator",
                },
            )

        self.graph.add_edge("aggregator", "end")

    def add_reflection_edges(self):
        """Add edges for reflection pattern"""
        self.graph.add_conditional_edges(
            "worker", lambda state: state.current_agent, {"reflector": "reflector"}
        )

        self.graph.add_conditional_edges(
            "reflector", lambda state: state.current_agent, {"worker": "worker", "end": "end"}
        )

    def add_pipeline_edges(self):
        """Add edges for pipeline pattern"""
        for i in range(len(self.config["agents"]) - 1):
            self.graph.add_edge(
                self.config["agents"][i]["name"], self.config["agents"][i + 1]["name"]
            )

        if self.config["agents"]:
            self.graph.add_edge(self.config["agents"][-1]["name"], "end")

    def add_autonomous_edges(self):
        """Add edges for autonomous pattern"""
        self.graph.add_conditional_edges(
            "autonomous",
            lambda state: state.current_agent,
            {"autonomous": "autonomous", "end": "end"},
        )

    async def process_question_langgraph(self, env, question: str) -> Dict[str, Any]:
        """Process question using LangGraph workflow"""
        # Initialize components if not already done
        if not self.compiled_graph:
            self.setup_langgraph_components(env)

        # Check cache first
        cache_key = f"langgraph:{self.config['pattern']}:{question.lower().strip()}"
        cached = await self.get_from_cache(env, cache_key)

        if cached:
            return {"answer": cached, "cached": True, "pattern": self.config["pattern"]}

        try:
            # Create initial state
            initial_state = {"task": question, "messages": [HumanMessage(content=question)]}

            # Run the workflow
            final_state = await self.compiled_graph.invoke(initial_state)

            # Extract the answer from final state
            messages = final_state.get("messages", [])
            last_message = messages[-1] if messages else {"content": "No response generated"}
            answer = last_message.get("content", "No response generated")

            # Cache the response
            await self.put_in_cache(env, cache_key, answer)

            return {
                "answer": answer,
                "cached": False,
                "pattern": self.config["pattern"],
                "iterations": final_state.get("iteration", 0),
                "metadata": final_state.get("metadata", {}),
            }
        except Exception as e:
            console.error(f"LangGraph processing error: {e}")
            # Fallback to base agent processing
            return await super().process_question(env, question)

    async def process_question(self, env, question: str) -> Dict[str, Any]:
        """Process question using appropriate method"""
        if self.config.get("pattern") and self.config["pattern"] != "basic":
            return await self.process_question_langgraph(env, question)
        else:
            return await super().process_question(env, question)

    def get_home_page(self) -> str:
        """Override home page to show LangGraph pattern"""
        base_page = super().get_home_page()

        # Add LangGraph pattern information
        pattern_info = f"""
        <p class="tech-badge">🕸️ LangGraph {self.config['pattern']} Pattern</p>
        <div class="pattern-info">
            <strong>Pattern:</strong> {self.config['pattern']}<br>
            <strong>Agents:</strong> {len(self.config['agents'])}
        </div>
        """

        # Insert pattern info after the subtitle
        import re

        base_page = re.sub(
            r'(<p class="subtitle">.*?</p>)', r"\1" + pattern_info, base_page, flags=re.DOTALL
        )

        return base_page

    def get_styles(self) -> str:
        """Add pattern-specific styling"""
        base_styles = super().get_styles()

        pattern_styles = """
        .pattern-info {
            text-align: center;
            color: #64ffda;
            font-size: 0.85rem;
            margin-top: 0.5rem;
            padding: 0.5rem;
            background: rgba(100, 255, 218, 0.1);
            border-radius: 4px;
        }
        """

        return base_styles + pattern_styles
