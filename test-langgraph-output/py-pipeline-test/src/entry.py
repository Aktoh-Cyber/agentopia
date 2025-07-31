# Auto-generated pipeline agent
# Generated from configuration at 2025-07-30T22:02:28.170421

from agent_framework.langgraph_agent import LangGraphAgent

# Configuration for pipeline-demo
config = {
    'type': 'pipeline',
    'name': 'pipeline-demo',
    'description': 'Sequential processing pipeline with specialized stages',
    'icon': '🔄',
    'subtitle': 'LangGraph Pipeline Pattern',
    'systemPrompt': """You process tasks through a sequential pipeline of specialized agents, each adding their expertise.""",
    'placeholder': 'Enter a task to process through the pipeline...',
    'examples': ["Process a new customer onboarding request", "Analyze a complex data transformation task", "Review and format a technical document"],
    'aiLabel': 'Pipeline Agent',
    'footer': 'Built with LangGraph and Cloudflare Workers AI',
    'domain': 'pipeline-demo.example.com',
    'model': '@cf/meta/llama-3.1-8b-instruct',
    'maxTokens': 1024,
    'temperature': 0.5,
    'cacheEnabled': true,
    'cacheTTL': 3600,
    'pattern': 'pipeline',
    'maxIterations': 5,
    'agents': [
  {
    "name": "intake",
    "expertise": "Requirements analysis, input validation, and task parsing",
    "description": "Processes initial input and prepares it for downstream stages"
  },
  {
    "name": "processor",
    "expertise": "Core logic, data transformation, and business rules",
    "description": "Applies main processing logic and transformations"
  },
  {
    "name": "validator",
    "expertise": "Quality assurance, error checking, and compliance verification",
    "description": "Validates output quality and compliance requirements"
  },
  {
    "name": "formatter",
    "expertise": "Output formatting, presentation, and delivery preparation",
    "description": "Formats final output for optimal presentation and delivery"
  }
],
    'useLangchain': true
}

# Create the pipeline agent
pipelinedemoagent = LangGraphAgent(config)

# Export the fetch handler
async def on_fetch(request, env):
    """Main request handler for Cloudflare Workers"""
    return await pipelinedemoagent.fetch(request, env)
