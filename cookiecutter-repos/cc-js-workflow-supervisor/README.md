# JavaScript Workflow Supervisor Agent Template

A cookiecutter template for creating JavaScript workflow supervisor agents that orchestrate multi-agent systems on Cloudflare Workers.

## Features

- **Workflow Orchestration**: Sequential, parallel, or custom workflow execution
- **Multi-Agent Coordination**: Manages specialist agents as workflow steps
- **Error Handling**: Retry logic, fallback strategies, and error recovery
- **State Management**: Maintains workflow state across agent calls
- **Progress Tracking**: Real-time workflow progress monitoring
- **MCP Protocol**: Full Model Context Protocol support
- **LangChain.js Integration**: Advanced chain patterns and memory management
- **Cloudflare Workers**: Serverless deployment with edge computing

## Quick Start

```bash
# Install cookiecutter
pip install cookiecutter

# Generate from template
cookiecutter https://github.com/Aktoh-Cyber/cc-js-workflow-supervisor

# Navigate to generated project
cd your-workflow-supervisor

# Install dependencies
npm install

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
| `project_name` | Human-readable project name | Workflow Supervisor Agent |
| `agent_class_name` | JavaScript class name | WorkflowSupervisor |
| `domain` | Custom domain for deployment | workflow-supervisor.example.com |
| `workflow_steps_json` | JSON array of workflow steps | Sequential analyze→process→validate |
| `specialist_agents_json` | JSON array of specialist agents | Three example agents |
| `supervisor_strategy` | Execution strategy | sequential |
| `error_handling` | Error handling strategy | retry_with_fallback |
| `max_retries` | Maximum retry attempts | 3 |
| `timeout_ms` | Workflow timeout in milliseconds | 30000 |

## Workflow Configuration

### Workflow Steps

Define your workflow as a JSON array of steps:

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
    "required": true,
    "parallel": false
  },
  {
    "name": "validate",
    "description": "Validate results",
    "agent": "validator",
    "required": false,
    "condition": "process.success === true"
  }
]
```

### Specialist Agents

Configure the specialist agents available to the workflow:

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
    "description": "Processes data",
    "headers": {
      "X-Custom-Header": "value"
    }
  }
]
```

## Supervisor Strategies

### Sequential (default)
Executes workflow steps one after another in order.

```javascript
// Steps execute: analyze → process → validate
strategy: "sequential"
```

### Parallel
Executes all steps simultaneously and waits for completion.

```javascript
// All steps execute at once
strategy: "parallel"
```

### Conditional
Executes steps based on conditions and previous results.

```javascript
// Steps execute based on conditions
strategy: "conditional"
```

### Map-Reduce
Distributes work across agents and aggregates results.

```javascript
// Distribute → Process → Aggregate
strategy: "map_reduce"
```

## Error Handling Strategies

### Retry with Fallback
Retries failed steps and falls back to alternative agents.

```javascript
error_handling: "retry_with_fallback"
max_retries: 3
```

### Circuit Breaker
Prevents cascading failures by stopping after threshold.

```javascript
error_handling: "circuit_breaker"
failure_threshold: 5
```

### Compensate
Runs compensation logic to undo partial changes.

```javascript
error_handling: "compensate"
```

## LangChain.js Integration

The supervisor uses LangChain.js for advanced orchestration:

```javascript
import { WorkflowSupervisor } from './workflow-supervisor.js';

const supervisor = new WorkflowSupervisor(config);

// Create a workflow chain
const workflowChain = supervisor.createWorkflowChain();

// Execute with context
const result = await workflowChain.call({
  question: "Complex multi-step task",
  context: previousResults
});

// Access workflow state
const state = supervisor.getWorkflowState();
console.log('Completed steps:', state.completedSteps);
console.log('Current step:', state.currentStep);
```

## Workflow State Management

The supervisor maintains state throughout workflow execution:

```javascript
{
  workflowId: "uuid",
  startTime: "2025-01-15T10:00:00Z",
  status: "in_progress",
  currentStep: "process",
  completedSteps: ["analyze"],
  stepResults: {
    analyze: { success: true, data: {...} }
  },
  errors: [],
  metadata: {}
}
```

## API Endpoints

### Main Endpoints

- `GET /` - Web interface with workflow visualization
- `POST /` - Process workflow requests
- `GET /health` - Health check with agent status
- `POST /mcp` - MCP protocol endpoint

### Workflow Control

- `GET /workflow/status` - Current workflow status
- `POST /workflow/cancel` - Cancel running workflow
- `GET /workflow/history` - Workflow execution history
- `POST /workflow/retry` - Retry failed workflow

## Monitoring and Observability

### Workflow Metrics

- Workflow execution time
- Step completion rates
- Agent response times
- Error rates by step
- Retry statistics

### Logging

Structured logging for workflow tracking:

```javascript
console.log({
  level: 'info',
  workflow_id: 'uuid',
  step: 'process',
  duration_ms: 1234,
  status: 'completed'
});
```

## Advanced Features

### Dynamic Workflow Modification

Modify workflows based on runtime conditions:

```javascript
supervisor.addStep({
  name: "review",
  agent: "reviewer",
  after: "process"
});

supervisor.removeStep("validate");
```

### Workflow Templates

Pre-defined workflow patterns:

- **Review-Approve**: Two-step approval workflow
- **ETL Pipeline**: Extract-Transform-Load pattern
- **Validation Chain**: Multi-level validation
- **Consensus**: Multiple agents vote on outcome

### State Persistence

Optional KV namespace for workflow state:

```toml
[[kv_namespaces]]
binding = "WORKFLOW_STATE"
id = "your-kv-namespace-id"
```

## Development

### Project Structure

```
your-workflow-supervisor/
├── src/
│   ├── index.js           # Main supervisor implementation
│   ├── workflow-engine.js # Workflow execution engine
│   ├── state-manager.js   # State management
│   └── agent-client.js    # Specialist agent communication
├── wrangler.toml          # Cloudflare configuration
├── package.json           # Dependencies
└── scripts/
    └── deploy.sh          # Deployment script
```

### Testing Workflows

```bash
# Test with mock agents
npm test

# Test specific workflow
npm test -- --workflow=analyze-process-validate

# Test error scenarios
npm test -- --scenario=agent-failure
```

### Local Development

The template includes mock agents for local testing:

```javascript
// Mock agents respond to workflow steps
const mockAgents = {
  analyst: async (data) => ({ analysis: "complete" }),
  processor: async (data) => ({ processed: true }),
  validator: async (data) => ({ valid: true })
};
```

## Best Practices

1. **Idempotent Steps**: Ensure workflow steps can be safely retried
2. **Timeout Configuration**: Set appropriate timeouts for each step
3. **Error Boundaries**: Handle errors at step and workflow levels
4. **State Checkpoints**: Save state after critical steps
5. **Monitoring**: Track workflow metrics and performance
6. **Documentation**: Document workflow logic and dependencies

## Integration Examples

### With Router Agent

```javascript
// Router forwards complex tasks to supervisor
const router = new RouterAgent({
  tools: [{
    name: "workflow_supervisor",
    endpoint: "https://your-supervisor.workers.dev",
    keywords: ["workflow", "multi-step", "complex"]
  }]
});
```

### With Specialist Agents

```javascript
// Specialists register with supervisor
POST /workflow/register
{
  "name": "data_processor",
  "endpoint": "https://processor.workers.dev",
  "capabilities": ["transform", "aggregate"]
}
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
  { pattern = "workflow-supervisor.example.com", zone_name = "example.com" }
]
```

### Production Checklist

- [ ] Configure production AI model
- [ ] Set up error alerting
- [ ] Configure workflow timeout
- [ ] Enable caching where appropriate
- [ ] Set up monitoring dashboard
- [ ] Document workflow patterns

## Support

- [Documentation](https://github.com/Aktoh-Cyber/cc-js-workflow-supervisor/wiki)
- [Issues](https://github.com/Aktoh-Cyber/cc-js-workflow-supervisor/issues)
- [Examples](https://github.com/Aktoh-Cyber/cc-js-workflow-supervisor/tree/main/examples)

## License

MIT License - See LICENSE file for details