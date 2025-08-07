/**
 * Workflow Engine
 * Manages workflow execution logic and step coordination
 */

export class WorkflowEngine {
  constructor(config) {
    this.steps = config.steps || [];
    this.agents = config.agents || [];
    this.strategy = config.strategy || 'sequential';
    this.errorHandling = config.errorHandling || 'retry_with_fallback';
    this.maxRetries = config.maxRetries || 3;
    this.timeout = config.timeout || 30000;
    
    // Track execution metrics
    this.metrics = {
      totalExecutions: 0,
      successfulExecutions: 0,
      failedExecutions: 0,
      averageExecutionTime: 0,
      stepMetrics: {}
    };
  }
  
  /**
   * Validate workflow configuration
   */
  validateWorkflow() {
    const errors = [];
    
    // Check for required agents
    for (const step of this.steps) {
      const agent = this.agents.find(a => a.name === step.agent);
      if (!agent) {
        errors.push(`Agent '${step.agent}' required by step '${step.name}' not found`);
      }
    }
    
    // Check for circular dependencies
    if (this.hasCircularDependencies()) {
      errors.push('Workflow contains circular dependencies');
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }
  
  /**
   * Check for circular dependencies in workflow
   */
  hasCircularDependencies() {
    const visited = new Set();
    const recursionStack = new Set();
    
    const hasCycle = (stepName) => {
      visited.add(stepName);
      recursionStack.add(stepName);
      
      const step = this.steps.find(s => s.name === stepName);
      if (step && step.dependsOn) {
        for (const dep of step.dependsOn) {
          if (!visited.has(dep)) {
            if (hasCycle(dep)) return true;
          } else if (recursionStack.has(dep)) {
            return true;
          }
        }
      }
      
      recursionStack.delete(stepName);
      return false;
    };
    
    for (const step of this.steps) {
      if (!visited.has(step.name)) {
        if (hasCycle(step.name)) return true;
      }
    }
    
    return false;
  }
  
  /**
   * Get execution order based on dependencies
   */
  getExecutionOrder() {
    const order = [];
    const visited = new Set();
    
    const visit = (stepName) => {
      if (visited.has(stepName)) return;
      visited.add(stepName);
      
      const step = this.steps.find(s => s.name === stepName);
      if (step && step.dependsOn) {
        for (const dep of step.dependsOn) {
          visit(dep);
        }
      }
      
      order.push(stepName);
    };
    
    for (const step of this.steps) {
      visit(step.name);
    }
    
    return order;
  }
  
  /**
   * Execute workflow with given strategy
   */
  async execute(context, strategy = this.strategy) {
    const startTime = Date.now();
    this.metrics.totalExecutions++;
    
    try {
      let result;
      
      switch (strategy) {
        case 'sequential':
          result = await this.executeSequential(context);
          break;
        case 'parallel':
          result = await this.executeParallel(context);
          break;
        case 'conditional':
          result = await this.executeConditional(context);
          break;
        case 'map_reduce':
          result = await this.executeMapReduce(context);
          break;
        default:
          throw new Error(`Unknown strategy: ${strategy}`);
      }
      
      this.metrics.successfulExecutions++;
      this.updateMetrics(Date.now() - startTime);
      
      return result;
      
    } catch (error) {
      this.metrics.failedExecutions++;
      throw error;
    }
  }
  
  /**
   * Execute steps sequentially
   */
  async executeSequential(context) {
    const results = {};
    const executionOrder = this.getExecutionOrder();
    
    for (const stepName of executionOrder) {
      const step = this.steps.find(s => s.name === stepName);
      if (!step) continue;
      
      // Check if step should be executed
      if (!this.shouldExecuteStep(step, results)) {
        continue;
      }
      
      // Execute step
      const stepResult = await this.executeStep(step, context, results);
      results[stepName] = stepResult;
      
      // Check if we should continue
      if (stepResult.stopWorkflow) {
        break;
      }
    }
    
    return results;
  }
  
  /**
   * Execute steps in parallel
   */
  async executeParallel(context) {
    const parallelGroups = this.getParallelGroups();
    const results = {};
    
    for (const group of parallelGroups) {
      const groupPromises = group.map(stepName => {
        const step = this.steps.find(s => s.name === stepName);
        if (!step || !this.shouldExecuteStep(step, results)) {
          return Promise.resolve(null);
        }
        
        return this.executeStep(step, context, results)
          .then(result => ({ stepName, result }));
      });
      
      const groupResults = await Promise.all(groupPromises);
      
      for (const { stepName, result } of groupResults) {
        if (result) {
          results[stepName] = result;
        }
      }
    }
    
    return results;
  }
  
  /**
   * Execute steps conditionally
   */
  async executeConditional(context) {
    const results = {};
    
    for (const step of this.steps) {
      // Evaluate condition
      if (!this.evaluateCondition(step.condition, context, results)) {
        continue;
      }
      
      // Execute step
      const stepResult = await this.executeStep(step, context, results);
      results[step.name] = stepResult;
      
      // Update context for next conditions
      context = { ...context, ...stepResult };
    }
    
    return results;
  }
  
  /**
   * Execute map-reduce pattern
   */
  async executeMapReduce(context) {
    // Map phase
    const mapSteps = this.steps.filter(s => s.phase === 'map');
    const mapPromises = mapSteps.map(step =>
      this.executeStep(step, context, {})
    );
    
    const mapResults = await Promise.all(mapPromises);
    
    // Reduce phase
    const reduceStep = this.steps.find(s => s.phase === 'reduce');
    if (reduceStep) {
      const reduceContext = { ...context, mapResults };
      const reduceResult = await this.executeStep(reduceStep, reduceContext, {});
      
      return {
        map: mapResults,
        reduce: reduceResult
      };
    }
    
    return { map: mapResults };
  }
  
  /**
   * Execute a single step
   */
  async executeStep(step, context, previousResults) {
    const startTime = Date.now();
    const stepMetrics = this.metrics.stepMetrics[step.name] || {
      executions: 0,
      failures: 0,
      totalTime: 0
    };
    
    try {
      // Find the agent for this step
      const agent = this.agents.find(a => a.name === step.agent);
      if (!agent) {
        throw new Error(`Agent ${step.agent} not found`);
      }
      
      // Prepare step context
      const stepContext = {
        ...context,
        previousResults,
        stepConfig: step
      };
      
      // Execute with timeout
      const result = await this.executeWithTimeout(
        () => this.callAgent(agent, stepContext),
        step.timeout || this.timeout
      );
      
      // Update metrics
      stepMetrics.executions++;
      stepMetrics.totalTime += Date.now() - startTime;
      this.metrics.stepMetrics[step.name] = stepMetrics;
      
      return result;
      
    } catch (error) {
      stepMetrics.failures++;
      this.metrics.stepMetrics[step.name] = stepMetrics;
      
      // Handle error based on configuration
      if (step.required !== false) {
        throw error;
      }
      
      return { error: error.message, skipped: false };
    }
  }
  
  /**
   * Call an agent
   */
  async callAgent(agent, context) {
    const response = await fetch(agent.endpoint, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...agent.headers
      },
      body: JSON.stringify(context)
    });
    
    if (!response.ok) {
      throw new Error(`Agent ${agent.name} returned ${response.status}`);
    }
    
    return await response.json();
  }
  
  /**
   * Execute with timeout
   */
  async executeWithTimeout(fn, timeout) {
    return Promise.race([
      fn(),
      new Promise((_, reject) =>
        setTimeout(() => reject(new Error('Operation timed out')), timeout)
      )
    ]);
  }
  
  /**
   * Check if step should be executed
   */
  shouldExecuteStep(step, previousResults) {
    // Check dependencies
    if (step.dependsOn) {
      for (const dep of step.dependsOn) {
        if (!previousResults[dep] || previousResults[dep].error) {
          return false;
        }
      }
    }
    
    // Check condition
    if (step.condition) {
      return this.evaluateCondition(step.condition, {}, previousResults);
    }
    
    return true;
  }
  
  /**
   * Evaluate a condition
   */
  evaluateCondition(condition, context, results) {
    if (!condition) return true;
    
    try {
      // Simple condition evaluation (can be extended)
      const fn = new Function('context', 'results', `return ${condition}`);
      return fn(context, results);
    } catch (error) {
      console.error('Condition evaluation failed:', error);
      return false;
    }
  }
  
  /**
   * Get parallel execution groups
   */
  getParallelGroups() {
    const groups = [];
    const visited = new Set();
    
    // Group steps that can run in parallel
    for (const step of this.steps) {
      if (visited.has(step.name)) continue;
      
      const group = [step.name];
      visited.add(step.name);
      
      // Find other steps that can run in parallel
      for (const other of this.steps) {
        if (visited.has(other.name)) continue;
        if (!this.dependsOn(other, step) && !this.dependsOn(step, other)) {
          group.push(other.name);
          visited.add(other.name);
        }
      }
      
      groups.push(group);
    }
    
    return groups;
  }
  
  /**
   * Check if step A depends on step B
   */
  dependsOn(stepA, stepB) {
    if (!stepA.dependsOn) return false;
    
    if (stepA.dependsOn.includes(stepB.name)) return true;
    
    // Check transitive dependencies
    for (const dep of stepA.dependsOn) {
      const depStep = this.steps.find(s => s.name === dep);
      if (depStep && this.dependsOn(depStep, stepB)) {
        return true;
      }
    }
    
    return false;
  }
  
  /**
   * Update execution metrics
   */
  updateMetrics(executionTime) {
    const total = this.metrics.successfulExecutions;
    const currentAvg = this.metrics.averageExecutionTime;
    
    this.metrics.averageExecutionTime = (currentAvg * (total - 1) + executionTime) / total;
  }
  
  /**
   * Get workflow metrics
   */
  getMetrics() {
    return {
      ...this.metrics,
      successRate: this.metrics.totalExecutions > 0
        ? this.metrics.successfulExecutions / this.metrics.totalExecutions
        : 0
    };
  }
}