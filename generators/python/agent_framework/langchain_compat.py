"""
LangChain-compatible interfaces using only Python standard library
Provides familiar LangChain-style abstractions for Cloudflare Workers
"""

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Union


@dataclass
class BaseMessage:
    """Base class for messages"""

    content: str
    additional_kwargs: dict[str, Any] = field(default_factory=dict)


@dataclass
class SystemMessage(BaseMessage):
    """System message"""

    role: str = "system"


@dataclass
class HumanMessage(BaseMessage):
    """Human/User message"""

    role: str = "user"


@dataclass
class AIMessage(BaseMessage):
    """AI/Assistant message"""

    role: str = "assistant"


class BasePromptTemplate(ABC):
    """Base class for prompt templates"""

    @abstractmethod
    def format(self, **kwargs: Any) -> str:
        """Format the prompt with the given variables"""
        pass

    @abstractmethod
    def format_messages(self, **kwargs: Any) -> list[BaseMessage]:
        """Format as messages"""
        pass


class PromptTemplate(BasePromptTemplate):
    """Simple prompt template with variable substitution"""

    def __init__(self, template: str, input_variables: Optional[list[str]] = None):
        self.template = template
        self.input_variables = input_variables or self._extract_variables(template)

    def _extract_variables(self, template: str) -> list[str]:
        """Extract variables from template string"""
        return list(set(re.findall(r"\{(\w+)\}", template)))

    def format(self, **kwargs: Any) -> str:
        """Format the template with provided variables"""
        return self.template.format(**kwargs)

    def format_messages(self, **kwargs: Any) -> list[BaseMessage]:
        """Format as a single human message"""
        return [HumanMessage(content=self.format(**kwargs))]


class ChatPromptTemplate(BasePromptTemplate):
    """Chat-style prompt template"""

    def __init__(self, messages: list[Union[BaseMessage, tuple]]):
        self.messages = []
        for msg in messages:
            if isinstance(msg, BaseMessage):
                self.messages.append(msg)
            elif isinstance(msg, tuple) and len(msg) == 2:
                role, content = msg
                if role == "system":
                    self.messages.append(SystemMessage(content=content))
                elif role == "user" or role == "human":
                    self.messages.append(HumanMessage(content=content))
                elif role == "assistant" or role == "ai":
                    self.messages.append(AIMessage(content=content))

    @classmethod
    def from_messages(cls, messages: list[Union[BaseMessage, tuple]]) -> "ChatPromptTemplate":
        """Create from messages"""
        return cls(messages)

    def format(self, **kwargs: Any) -> str:
        """Format as string (concatenated messages)"""
        formatted_messages = self.format_messages(**kwargs)
        return "\n\n".join([f"{msg.role}: {msg.content}" for msg in formatted_messages])

    def format_messages(self, **kwargs: Any) -> list[BaseMessage]:
        """Format messages with variables"""
        formatted = []
        for msg in self.messages:
            content = msg.content
            # Simple variable substitution
            for key, value in kwargs.items():
                content = content.replace(f"{{{key}}}", str(value))

            if isinstance(msg, SystemMessage):
                formatted.append(SystemMessage(content=content))
            elif isinstance(msg, HumanMessage):
                formatted.append(HumanMessage(content=content))
            elif isinstance(msg, AIMessage):
                formatted.append(AIMessage(content=content))

        return formatted


class BaseLLM(ABC):
    """Base LLM interface"""

    @abstractmethod
    async def agenerate(self, messages: list[BaseMessage], **kwargs: Any) -> str:
        """Generate response from messages"""
        pass

    async def ainvoke(self, input: Union[str, list[BaseMessage]], **kwargs: Any) -> str:
        """Invoke the LLM"""
        if isinstance(input, str):
            messages = [HumanMessage(content=input)]
        else:
            messages = input
        return await self.agenerate(messages, **kwargs)


class CloudflareLLM(BaseLLM):
    """Cloudflare Workers AI LLM implementation"""

    def __init__(
        self,
        model: str = "@cf/meta/llama-3.1-8b-instruct",
        temperature: float = 0.3,
        max_tokens: int = 512,
        **kwargs: Any,
    ):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.model_kwargs = kwargs

    async def agenerate(self, messages: list[BaseMessage], **kwargs: Any) -> str:
        """Generate using Cloudflare AI"""
        # This will be implemented in the actual agent to use env.AI
        # For now, return a placeholder
        raise NotImplementedError("Must be implemented with access to env.AI")


class BaseChain(ABC):
    """Base class for chains"""

    @abstractmethod
    async def arun(self, **kwargs: Any) -> Any:
        """Run the chain"""
        pass

    async def ainvoke(self, input: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
        """Invoke the chain"""
        result = await self.arun(**input, **kwargs)
        return {"output": result}


class LLMChain(BaseChain):
    """Simple LLM chain with prompt template"""

    def __init__(self, llm: BaseLLM, prompt: BasePromptTemplate):
        self.llm = llm
        self.prompt = prompt

    async def arun(self, **kwargs: Any) -> str:
        """Run the chain"""
        messages = self.prompt.format_messages(**kwargs)
        return await self.llm.ainvoke(messages)


class SimpleSequentialChain(BaseChain):
    """Chain that runs multiple chains in sequence"""

    def __init__(self, chains: list[BaseChain]):
        self.chains = chains

    async def arun(self, **kwargs: Any) -> Any:
        """Run chains in sequence"""
        result = kwargs.get("input", "")
        for chain in self.chains:
            result = await chain.arun(input=result)
        return result


class ConversationBufferMemory:
    """Simple conversation memory"""

    def __init__(self, memory_key: str = "history", return_messages: bool = True):
        self.memory_key = memory_key
        self.return_messages = return_messages
        self.messages: list[BaseMessage] = []

    def add_user_message(self, message: str):
        """Add user message to memory"""
        self.messages.append(HumanMessage(content=message))

    def add_ai_message(self, message: str):
        """Add AI message to memory"""
        self.messages.append(AIMessage(content=message))

    def clear(self):
        """Clear memory"""
        self.messages = []

    def get_messages(self) -> list[BaseMessage]:
        """Get all messages"""
        return self.messages.copy()

    def load_memory_variables(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Load memory variables"""
        if self.return_messages:
            return {self.memory_key: self.messages}
        else:
            # Return as string
            history = "\n".join([f"{msg.role}: {msg.content}" for msg in self.messages])
            return {self.memory_key: history}


class BaseOutputParser(ABC):
    """Base output parser"""

    @abstractmethod
    def parse(self, text: str) -> Any:
        """Parse the output"""
        pass


class StrOutputParser(BaseOutputParser):
    """Simple string output parser"""

    def parse(self, text: str) -> str:
        """Return text as-is"""
        return text.strip()


class JsonOutputParser(BaseOutputParser):
    """JSON output parser"""

    def parse(self, text: str) -> dict[str, Any]:
        """Parse JSON from text"""
        try:
            # Try to extract JSON from markdown code blocks
            json_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
            if json_match:
                text = json_match.group(1)
            return json.loads(text.strip())
        except json.JSONDecodeError:
            return {"error": "Failed to parse JSON", "raw": text}


class AgentExecutor:
    """Simple agent executor"""

    def __init__(
        self,
        agent: "BaseAgent",
        tools: list[Any],
        memory: Optional[ConversationBufferMemory] = None,
    ):
        self.agent = agent
        self.tools = tools
        self.memory = memory

    async def arun(self, input: str, **kwargs: Any) -> str:
        """Run the agent"""
        # Add to memory if available
        if self.memory:
            self.memory.add_user_message(input)

        # Get response from agent
        response = await self.agent.arun(input, **kwargs)

        # Add to memory if available
        if self.memory:
            self.memory.add_ai_message(response)

        return response
