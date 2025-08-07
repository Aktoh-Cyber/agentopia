# Python Workflow Supervisor Agent Template

A cookiecutter template for creating Python workflow supervisor agents that orchestrate multi-agent systems on Cloudflare Workers using Pyodide runtime.

## Features

- **Workflow Orchestration**: Sequential, parallel, or custom workflow execution
- **Multi-Agent Coordination**: Manages specialist agents as workflow steps
- **Error Handling**: Retry logic, fallback strategies, and error recovery
- **State Management**: Maintains workflow state across agent calls
- **Progress Tracking**: Real-time workflow progress monitoring
- **MCP Protocol**: Full Model Context Protocol support
- **Pyodide Runtime**: Python execution in Cloudflare Workers
- **Standard Library Only**: Production-ready with no external dependencies

## Quick Start

```bash
# Install cookiecutter
pip install cookiecutter

# Generate from template
cookiecutter https://github.com/Aktoh-Cyber/cc-py-workflow-supervisor

# Navigate to generated project
cd your-workflow-supervisor

# Install development dependencies
pip install -e .[dev]

# Install Wrangler CLI
npm install -g wrangler

# Configure environment
cp .env.local.example .env.local
# Edit .env.local with your Cloudflare credentials

# Run locally
npx wrangler dev

# Deploy to production
export CLOUDFLARE_API_TOKEN="your-token"
./scripts/deploy.sh
```

## Template Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `project_name` | Human-readable project name | Python Workflow Supervisor |
| `agent_class_name` | Python class name | WorkflowSupervisor |
| `domain` | Custom domain for deployment | py-workflow-supervisor.example.com |
| `workflow_steps_json` | JSON array of workflow steps | Sequential analyze→process→validate |
| `specialist_agents_json` | JSON array of specialist agents | Three example agents |
| `supervisor_strategy` | Execution strategy | sequential |
| `error_handling` | Error handling strategy | retry_with_fallback |
| `max_retries` | Maximum retry attempts | 3 |
| `timeout_ms` | Workflow timeout in milliseconds | 30000 |

## Python on Cloudflare Workers

This template uses Pyodide to run Python in Cloudflare Workers:

### Production Constraints
- **Standard Library Only**: External packages not available in production
- **FFI Imports**: Use `from js import fetch, Response, Headers, console`
- **Async/Await**: Full support for asynchronous operations
- **Type Hints**: Supported and recommended

### Development Environment
- Full Python package support for local development
- Type checking with mypy
- Code formatting with black
- Testing with pytest

## Workflow Configuration

### Workflow Steps

Define your workflow as a JSON array:

```json
[
  {
    "name": "analyze",
    "description": "Analyze the request",
    "agent": "analyst",
    "required": true,
    "timeout": 10000
  },
  {
    "name": "process",
    "description": "Process the data",
    "agent": "processor",
    "depends_on": ["analyze"]
  },
  {
    "name": "validate",
    "description": "Validate results",
    "agent": "validator",
    "condition": "results.process.success == True"
  }
]
```

### Specialist Agents

Configure available agents:

```json
[
  {
    "name": "analyst",
    "endpoint": "https://analyst.example.com",
    "description": "Analyzes requests",
    "timeout": 5000,
    "retries": 2
  },
  {
    "name": "processor",
    "endpoint": "https://processor.example.com",
    "description": "Processes data"
  }
]
```

## Supervisor Strategies

### Sequential (default)
```python
# Steps execute one after another
strategy = "sequential"
# analyze → process → validate
```

### Parallel
```python
# All steps execute simultaneously
strategy = "parallel"
# analyze + process + validate (all at once)
```

### Conditional
```python
# Steps execute based on conditions
strategy = "conditional"
# if condition: step1 else: step2
```

### Map-Reduce
```python
# Distribute work and aggregate results
strategy = "map_reduce"
# map(agents) → reduce(results)
```

## Implementation Example

```python
from agent_framework.workflow_supervisor import WorkflowSupervisor
from js import fetch, Response, Headers

class CustomWorkflowSupervisor(WorkflowSupervisor):
    """Custom workflow supervisor implementation."""
    
    async def analyze_request(self, question: str) -> dict:
        """Analyze incoming request to determine workflow."""
        # Custom analysis logic
        return {
            "required_steps": ["analyze", "process"],
            "complexity": "medium"
        }
    
    async def aggregate_results(self, results: dict) -> str:
        """Aggregate results from multiple agents."""
        # Custom aggregation logic
        return "Aggregated response"
    
    async def handle_error(self, error: Exception, context: dict) -> dict:
        """Custom error handling."""
        if self.error_handling == "retry_with_fallback":
            return await self.retry_with_fallback(context)
        return {"error": str(error)}
```

## State Management

The supervisor maintains workflow state throughout execution:

```python
{
    "workflow_id": "uuid",
    "status": "in_progress",
    "current_step": "process",
    "completed_steps": ["analyze"],
    "step_results": {
        "analyze": {"success": True, "data": {...}}
    },
    "errors": [],
    "metadata": {}
}
```

## API Endpoints

### Main Endpoints
- `GET /` - Web interface with workflow visualization
- `POST /` - Process workflow requests
- `GET /health` - Health check
- `POST /mcp` - MCP protocol endpoint

### Workflow Control
- `GET /workflow/status?id=<workflow_id>` - Get workflow status
- `POST /workflow/cancel` - Cancel running workflow
- `GET /workflow/history` - List workflow history
- `POST /workflow/retry` - Retry failed workflow

## Error Handling Strategies

### Retry with Fallback
```python
error_handling = "retry_with_fallback"
max_retries = 3
# Retries failed steps, falls back to alternative agents
```

### Circuit Breaker
```python
error_handling = "circuit_breaker"
failure_threshold = 5
# Stops after threshold to prevent cascading failures
```

### Compensate
```python
error_handling = "compensate"
# Runs compensation logic to undo partial changes
```

## Development

### Project Structure
```
your-workflow-supervisor/
├── src/
│   └── entry.py                  # Main supervisor implementation
├── agent_framework/
│   ├── __init__.py
│   ├── base_agent.py             # Base agent class
│   ├── workflow_supervisor.py    # Workflow orchestration
│   ├── workflow_engine.py        # Execution engine
│   └── state_manager.py          # State management
├── wrangler.toml                 # Cloudflare configuration
├── pyproject.toml                # Python dependencies
└── scripts/
    └── deploy.sh                 # Deployment script
```

### Testing Workflows

```bash
# Run tests locally
pytest tests/

# Test specific workflow
pytest tests/test_sequential_workflow.py

# Test with coverage
pytest --cov=agent_framework tests/
```

### Local Development

```bash
# Install development dependencies
pip install -e .[dev]

# Format code
black src/ agent_framework/

# Type checking
mypy src/ agent_framework/

# Run locally with mock agents
npx wrangler dev
```

## Monitoring and Observability

### Metrics
- Workflow execution time
- Step completion rates
- Agent response times
- Error rates by step
- Retry statistics

### Logging
```python
from js import console

console.log({
    "level": "info",
    "workflow_id": workflow_id,
    "step": current_step,
    "duration_ms": duration,
    "status": "completed"
})
```

## Python-Specific Considerations

### FFI Imports
```python
from js import fetch, Response, Headers, console, JSON, Object

# Use JavaScript APIs
response = await fetch(url)
data = await response.json()
```

### Type Hints
```python
from typing import Dict, List, Optional, Any

async def process_workflow(
    self, 
    question: str,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Process workflow with type safety."""
    pass
```

### Async/Await
```python
async def execute_step(self, step: dict) -> dict:
    """Execute workflow step asynchronously."""
    result = await self.call_agent(step["agent"], question)
    return result
```

## Best Practices

1. **Idempotent Steps**: Ensure steps can be safely retried
2. **Type Hints**: Use throughout for better code clarity
3. **Error Boundaries**: Handle errors at step and workflow levels
4. **State Checkpoints**: Save state after critical steps
5. **Documentation**: Document workflow logic and dependencies
6. **Standard Library**: Stick to standard library for production

## Integration Examples

### With Router Agent
```python
# Router forwards complex tasks to supervisor
router_config = {
    "tools": [{
        "name": "workflow_supervisor",
        "endpoint": "https://your-supervisor.workers.dev",
        "keywords": ["workflow", "multi-step", "complex"]
    }]
}
```

### With Specialist Agents
```python
# Register specialist with supervisor
await supervisor.register_agent({
    "name": "data_processor",
    "endpoint": "https://processor.workers.dev",
    "capabilities": ["transform", "aggregate"]
})
```

## Deployment

### Environment Variables
```bash
CLOUDFLARE_API_TOKEN=your_token
CLOUDFLARE_ACCOUNT_ID=your_account_id
```

### Custom Domain Setup
```toml
[env.production]
routes = [
  { pattern = "py-workflow-supervisor.example.com", zone_name = "example.com" }
]
```

### Production Checklist
- [ ] Configure production AI model
- [ ] Set up error alerting
- [ ] Configure workflow timeout
- [ ] Enable caching where appropriate
- [ ] Test with production endpoints
- [ ] Document workflow patterns

## Limitations

### Pyodide Runtime
- Standard library only in production
- Some Python packages may not be compatible
- Performance considerations for heavy computations

### Workarounds
- Use JavaScript APIs via FFI when needed
- Implement algorithms using standard library
- Offload heavy computation to specialist agents

## Support

- [Documentation](https://github.com/Aktoh-Cyber/cc-py-workflow-supervisor/wiki)
- [Issues](https://github.com/Aktoh-Cyber/cc-py-workflow-supervisor/issues)
- [Examples](https://github.com/Aktoh-Cyber/cc-py-workflow-supervisor/tree/main/examples)

## License

MIT License - See LICENSE file for details