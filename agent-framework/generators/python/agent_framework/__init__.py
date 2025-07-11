"""
Agent Framework for Python Cloudflare Workers
"""

__version__ = "1.0.0"

from .base_agent import BaseAgent
from .router_agent import RouterAgent
from .tool_registry import ToolRegistry, DynamicMCPClient
from .generator_agent import GeneratorAgent
from .enhanced_agent_generator import EnhancedAgentGenerator
from .github_client import GitHubMCPClient

__all__ = [
    'BaseAgent', 
    'RouterAgent', 
    'ToolRegistry', 
    'DynamicMCPClient',
    'GeneratorAgent',
    'EnhancedAgentGenerator', 
    'GitHubMCPClient'
]