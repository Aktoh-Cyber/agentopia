/**
 * {{ cookiecutter.project_name }}
 * {{ cookiecutter.description }}
 * 
 * This supervisor orchestrates multi-agent workflows on Cloudflare Workers
 */

import { ChatPromptTemplate } from "@langchain/core/prompts";
import { RunnableSequence } from "@langchain/core/runnables";
import { BaseAgent } from './base-agent.js';
import { WorkflowEngine } from './workflow-engine.js';
import { StateManager } from './state-manager.js';

export class {{ cookiecutter.agent_class_name }} extends BaseAgent {
  constructor(config) {
    // Supervisor configuration
    const supervisorConfig = {
      name: '{{ cookiecutter.project_name }}',
      description: '{{ cookiecutter.description }}',
      icon: '🎭',
      subtitle: 'Orchestrating multi-agent workflows',
      systemPrompt: `You are a workflow supervisor that orchestrates multi-agent systems.
      
Your responsibilities:
1. Analyze incoming requests and determine the appropriate workflow
2. Coordinate specialist agents to complete workflow steps
3. Monitor workflow progress and handle errors
4. Aggregate results from multiple agents
5. Ensure workflow completion or graceful failure

Workflow strategy: {{ cookiecutter.supervisor_strategy }}
Error handling: {{ cookiecutter.error_handling }}

Available workflow steps:
{{ cookiecutter.workflow_steps_json }}

Available specialist agents:
{{ cookiecutter.specialist_agents_json }}

Provide clear status updates and aggregate results from all agents.`,
      placeholder: 'Describe your complex task...',
      aiLabel: 'Workflow Supervisor',
      model: '{{ cookiecutter.ai_model }}',
      maxTokens: {{ cookiecutter.max_tokens }},
      temperature: {{ cookiecutter.temperature }},
      cacheEnabled: true,
      cacheTTL: {{ cookiecutter.cache_ttl }},
      ...config
    };
    
    super(supervisorConfig);
    
    // Initialize workflow components
    this.workflowSteps = {{ cookiecutter.workflow_steps_json }};
    this.specialistAgents = {{ cookiecutter.specialist_agents_json }};
    this.supervisorStrategy = '{{ cookiecutter.supervisor_strategy }}';
    this.errorHandling = '{{ cookiecutter.error_handling }}';
    this.maxRetries = {{ cookiecutter.max_retries }};
    this.timeoutMs = {{ cookiecutter.timeout_ms }};
    
    // Initialize workflow engine and state manager
    this.workflowEngine = new WorkflowEngine({
      steps: this.workflowSteps,
      agents: this.specialistAgents,
      strategy: this.supervisorStrategy,
      errorHandling: this.errorHandling,
      maxRetries: this.maxRetries,
      timeout: this.timeoutMs
    });
    
    this.stateManager = new StateManager();
  }
  
  /**
   * Process request through workflow
   */
  async processQuestion(env, question) {
    const workflowId = crypto.randomUUID();
    
    try {
      // Initialize workflow state
      const state = await this.stateManager.initializeWorkflow(workflowId, {
        question,
        strategy: this.supervisorStrategy,
        steps: this.workflowSteps
      });
      
      // Analyze request and determine workflow
      const analysis = await this.analyzeRequest(env, question);
      
      // Execute workflow based on strategy
      let result;
      switch (this.supervisorStrategy) {
        case 'sequential':
          result = await this.executeSequentialWorkflow(env, workflowId, question, analysis);
          break;
        case 'parallel':
          result = await this.executeParallelWorkflow(env, workflowId, question, analysis);
          break;
        case 'conditional':
          result = await this.executeConditionalWorkflow(env, workflowId, question, analysis);
          break;
        case 'map_reduce':
          result = await this.executeMapReduceWorkflow(env, workflowId, question, analysis);
          break;
        default:
          result = await this.executeSequentialWorkflow(env, workflowId, question, analysis);
      }
      
      // Update final state
      await this.stateManager.completeWorkflow(workflowId, result);
      
      return {
        response: result.aggregatedResponse,
        workflowId,
        completedSteps: result.completedSteps,
        duration: result.duration,
        metadata: {
          strategy: this.supervisorStrategy,
          stepsExecuted: result.stepsExecuted,
          errors: result.errors
        }
      };
      
    } catch (error) {
      console.error('Workflow execution error:', error);
      await this.stateManager.failWorkflow(workflowId, error);
      
      // Apply error handling strategy
      return await this.handleWorkflowError(env, workflowId, error, question);
    }
  }
  
  /**
   * Analyze request to determine workflow path
   */
  async analyzeRequest(env, question) {
    const prompt = ChatPromptTemplate.fromTemplate(`
Analyze this request and determine the appropriate workflow steps:

Request: {question}

Available steps: {steps}
Available agents: {agents}

Provide a JSON response with:
1. requiredSteps: Array of step names to execute
2. reasoning: Brief explanation of workflow choice
3. expectedDuration: Estimated time in ms
4. complexity: low/medium/high
`);
    
    const chain = RunnableSequence.from([
      prompt,
      this.llm,
      (response) => {
        try {
          return JSON.parse(response.content);
        } catch {
          return {
            requiredSteps: this.workflowSteps.map(s => s.name),
            reasoning: "Executing default workflow",
            expectedDuration: this.timeoutMs,
            complexity: "medium"
          };
        }
      }
    ]);
    
    return await chain.invoke({
      question,
      steps: JSON.stringify(this.workflowSteps),
      agents: JSON.stringify(this.specialistAgents)
    });
  }
  
  /**
   * Execute sequential workflow
   */
  async executeSequentialWorkflow(env, workflowId, question, analysis) {
    const startTime = Date.now();
    const completedSteps = [];
    const stepResults = {};
    const errors = [];
    
    for (const step of analysis.requiredSteps) {
      const stepConfig = this.workflowSteps.find(s => s.name === step);
      if (!stepConfig) continue;
      
      try {
        // Update state for current step
        await this.stateManager.startStep(workflowId, step);
        
        // Execute step with appropriate agent
        const agent = this.specialistAgents.find(a => a.name === stepConfig.agent);
        if (!agent) {
          throw new Error(`Agent ${stepConfig.agent} not found for step ${step}`);
        }
        
        // Call specialist agent
        const stepResult = await this.callSpecialistAgent(
          agent,
          question,
          stepResults,
          env
        );
        
        stepResults[step] = stepResult;
        completedSteps.push(step);
        
        // Update state with step completion
        await this.stateManager.completeStep(workflowId, step, stepResult);
        
      } catch (error) {
        console.error(`Step ${step} failed:`, error);
        errors.push({ step, error: error.message });
        
        // Handle step failure based on strategy
        if (this.errorHandling === 'retry_with_fallback') {
          const retryResult = await this.retryStep(step, stepConfig, question, stepResults, env);
          if (retryResult.success) {
            stepResults[step] = retryResult.data;
            completedSteps.push(step);
          } else if (stepConfig.required !== false) {
            throw new Error(`Required step ${step} failed after retries`);
          }
        } else if (stepConfig.required !== false) {
          throw error;
        }
      }
    }
    
    // Aggregate results
    const aggregatedResponse = await this.aggregateResults(stepResults, question, env);
    
    return {
      aggregatedResponse,
      completedSteps,
      stepsExecuted: Object.keys(stepResults).length,
      duration: Date.now() - startTime,
      errors,
      stepResults
    };
  }
  
  /**
   * Execute parallel workflow
   */
  async executeParallelWorkflow(env, workflowId, question, analysis) {
    const startTime = Date.now();
    
    // Create promises for all steps
    const stepPromises = analysis.requiredSteps.map(async (step) => {
      const stepConfig = this.workflowSteps.find(s => s.name === step);
      if (!stepConfig) return null;
      
      const agent = this.specialistAgents.find(a => a.name === stepConfig.agent);
      if (!agent) return null;
      
      try {
        await this.stateManager.startStep(workflowId, step);
        const result = await this.callSpecialistAgent(agent, question, {}, env);
        await this.stateManager.completeStep(workflowId, step, result);
        return { step, result, success: true };
      } catch (error) {
        return { step, error: error.message, success: false };
      }
    });
    
    // Wait for all steps to complete
    const results = await Promise.all(stepPromises);
    
    // Process results
    const stepResults = {};
    const completedSteps = [];
    const errors = [];
    
    for (const result of results) {
      if (!result) continue;
      if (result.success) {
        stepResults[result.step] = result.result;
        completedSteps.push(result.step);
      } else {
        errors.push({ step: result.step, error: result.error });
      }
    }
    
    // Aggregate results
    const aggregatedResponse = await this.aggregateResults(stepResults, question, env);
    
    return {
      aggregatedResponse,
      completedSteps,
      stepsExecuted: Object.keys(stepResults).length,
      duration: Date.now() - startTime,
      errors,
      stepResults
    };
  }
  
  /**
   * Execute conditional workflow
   */
  async executeConditionalWorkflow(env, workflowId, question, analysis) {
    // Implementation for conditional workflow execution
    // Evaluates conditions to determine next steps
    return this.executeSequentialWorkflow(env, workflowId, question, analysis);
  }
  
  /**
   * Execute map-reduce workflow
   */
  async executeMapReduceWorkflow(env, workflowId, question, analysis) {
    const startTime = Date.now();
    
    // Map phase: distribute work
    const mapTasks = this.specialistAgents.map(agent => ({
      agent,
      task: this.createMapTask(question, agent)
    }));
    
    // Execute map tasks in parallel
    const mapResults = await Promise.all(
      mapTasks.map(({ agent, task }) =>
        this.callSpecialistAgent(agent, task, {}, env)
          .catch(error => ({ error: error.message, agent: agent.name }))
      )
    );
    
    // Reduce phase: aggregate results
    const aggregatedResponse = await this.reduceResults(mapResults, question, env);
    
    return {
      aggregatedResponse,
      completedSteps: ['map', 'reduce'],
      stepsExecuted: mapTasks.length + 1,
      duration: Date.now() - startTime,
      errors: mapResults.filter(r => r.error),
      stepResults: { map: mapResults, reduce: aggregatedResponse }
    };
  }
  
  /**
   * Call a specialist agent
   */
  async callSpecialistAgent(agent, question, context, env) {
    const timeout = agent.timeout || 10000;
    const retries = agent.retries || this.maxRetries;
    
    for (let attempt = 0; attempt < retries; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        
        const response = await fetch(agent.endpoint, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...agent.headers
          },
          body: JSON.stringify({
            question,
            context,
            workflowMetadata: {
              supervisor: '{{ cookiecutter.project_name }}',
              strategy: this.supervisorStrategy
            }
          }),
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (!response.ok) {
          throw new Error(`Agent ${agent.name} returned ${response.status}`);
        }
        
        const result = await response.json();
        return result;
        
      } catch (error) {
        console.error(`Agent ${agent.name} attempt ${attempt + 1} failed:`, error);
        if (attempt === retries - 1) throw error;
        await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)));
      }
    }
  }
  
  /**
   * Retry a failed step
   */
  async retryStep(step, stepConfig, question, context, env) {
    for (let attempt = 0; attempt < this.maxRetries; attempt++) {
      try {
        const agent = this.specialistAgents.find(a => a.name === stepConfig.agent);
        const result = await this.callSpecialistAgent(agent, question, context, env);
        return { success: true, data: result };
      } catch (error) {
        console.error(`Retry ${attempt + 1} for step ${step} failed:`, error);
      }
    }
    return { success: false };
  }
  
  /**
   * Aggregate results from multiple agents
   */
  async aggregateResults(stepResults, question, env) {
    const prompt = ChatPromptTemplate.fromTemplate(`
Aggregate and synthesize these workflow results into a comprehensive response:

Original Question: {question}

Step Results:
{stepResults}

Provide a unified, coherent response that:
1. Addresses the original question completely
2. Incorporates insights from all workflow steps
3. Highlights key findings and recommendations
4. Notes any conflicts or uncertainties
`);
    
    const chain = RunnableSequence.from([
      prompt,
      this.llm
    ]);
    
    const response = await chain.invoke({
      question,
      stepResults: JSON.stringify(stepResults, null, 2)
    });
    
    return response.content;
  }
  
  /**
   * Create map task for agent
   */
  createMapTask(question, agent) {
    return `Process this question from your perspective as ${agent.description}: ${question}`;
  }
  
  /**
   * Reduce results from map phase
   */
  async reduceResults(mapResults, question, env) {
    const validResults = mapResults.filter(r => !r.error);
    return this.aggregateResults(
      Object.fromEntries(validResults.map((r, i) => [`map_${i}`, r])),
      question,
      env
    );
  }
  
  /**
   * Handle workflow errors
   */
  async handleWorkflowError(env, workflowId, error, question) {
    console.error(`Workflow ${workflowId} failed:`, error);
    
    switch (this.errorHandling) {
      case 'retry_with_fallback':
        return {
          response: `I encountered an error processing your request. ${error.message}. Please try rephrasing or simplifying your request.`,
          workflowId,
          error: error.message,
          status: 'failed_with_fallback'
        };
        
      case 'circuit_breaker':
        // Implement circuit breaker logic
        return {
          response: 'The workflow system is temporarily unavailable. Please try again later.',
          workflowId,
          error: 'Circuit breaker activated',
          status: 'circuit_broken'
        };
        
      case 'compensate':
        // Implement compensation logic
        await this.compensateWorkflow(workflowId);
        return {
          response: 'The workflow failed and has been rolled back. Please try again.',
          workflowId,
          error: error.message,
          status: 'compensated'
        };
        
      default:
        return {
          response: `Workflow execution failed: ${error.message}`,
          workflowId,
          error: error.message,
          status: 'failed'
        };
    }
  }
  
  /**
   * Compensate for failed workflow
   */
  async compensateWorkflow(workflowId) {
    const state = await this.stateManager.getWorkflowState(workflowId);
    // Implement compensation logic based on completed steps
    console.log(`Compensating workflow ${workflowId}`, state);
  }
  
  /**
   * Get workflow status
   */
  async getWorkflowStatus(workflowId) {
    return await this.stateManager.getWorkflowState(workflowId);
  }
  
  /**
   * Create workflow chain for LangChain integration
   */
  createWorkflowChain() {
    return RunnableSequence.from([
      (input) => ({ ...input, workflowId: crypto.randomUUID() }),
      async (input) => {
        const result = await this.processQuestion(input.env, input.question);
        return result;
      }
    ]);
  }
}

// Export default handler for Cloudflare Workers
export default {
  async fetch(request, env, ctx) {
    const supervisor = new {{ cookiecutter.agent_class_name }}();
    return supervisor.handleRequest(request, env, ctx);
  }
};