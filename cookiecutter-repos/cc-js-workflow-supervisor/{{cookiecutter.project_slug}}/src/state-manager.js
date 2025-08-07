/**
 * State Manager
 * Manages workflow state and persistence
 */

export class StateManager {
  constructor(kvNamespace = null) {
    this.kvNamespace = kvNamespace;
    this.inMemoryState = new Map();
    this.stateHistory = new Map();
  }
  
  /**
   * Initialize a new workflow
   */
  async initializeWorkflow(workflowId, config) {
    const state = {
      workflowId,
      status: 'initialized',
      startTime: new Date().toISOString(),
      config,
      currentStep: null,
      completedSteps: [],
      failedSteps: [],
      stepResults: {},
      errors: [],
      metadata: {},
      checkpoints: []
    };
    
    await this.saveState(workflowId, state);
    return state;
  }
  
  /**
   * Start a workflow step
   */
  async startStep(workflowId, stepName) {
    const state = await this.getState(workflowId);
    if (!state) throw new Error(`Workflow ${workflowId} not found`);
    
    state.currentStep = stepName;
    state.stepResults[stepName] = {
      status: 'in_progress',
      startTime: new Date().toISOString()
    };
    
    await this.saveState(workflowId, state);
    return state;
  }
  
  /**
   * Complete a workflow step
   */
  async completeStep(workflowId, stepName, result) {
    const state = await this.getState(workflowId);
    if (!state) throw new Error(`Workflow ${workflowId} not found`);
    
    state.completedSteps.push(stepName);
    state.stepResults[stepName] = {
      ...state.stepResults[stepName],
      status: 'completed',
      endTime: new Date().toISOString(),
      result,
      duration: this.calculateDuration(
        state.stepResults[stepName].startTime,
        new Date().toISOString()
      )
    };
    
    // Clear current step if it matches
    if (state.currentStep === stepName) {
      state.currentStep = null;
    }
    
    await this.saveState(workflowId, state);
    return state;
  }
  
  /**
   * Fail a workflow step
   */
  async failStep(workflowId, stepName, error) {
    const state = await this.getState(workflowId);
    if (!state) throw new Error(`Workflow ${workflowId} not found`);
    
    state.failedSteps.push(stepName);
    state.errors.push({
      step: stepName,
      error: error.message || error,
      timestamp: new Date().toISOString()
    });
    
    state.stepResults[stepName] = {
      ...state.stepResults[stepName],
      status: 'failed',
      endTime: new Date().toISOString(),
      error: error.message || error
    };
    
    // Clear current step if it matches
    if (state.currentStep === stepName) {
      state.currentStep = null;
    }
    
    await this.saveState(workflowId, state);
    return state;
  }
  
  /**
   * Complete entire workflow
   */
  async completeWorkflow(workflowId, result) {
    const state = await this.getState(workflowId);
    if (!state) throw new Error(`Workflow ${workflowId} not found`);
    
    state.status = 'completed';
    state.endTime = new Date().toISOString();
    state.result = result;
    state.duration = this.calculateDuration(state.startTime, state.endTime);
    
    await this.saveState(workflowId, state);
    await this.archiveWorkflow(workflowId);
    
    return state;
  }
  
  /**
   * Fail entire workflow
   */
  async failWorkflow(workflowId, error) {
    const state = await this.getState(workflowId);
    if (!state) throw new Error(`Workflow ${workflowId} not found`);
    
    state.status = 'failed';
    state.endTime = new Date().toISOString();
    state.error = error.message || error;
    state.duration = this.calculateDuration(state.startTime, state.endTime);
    
    await this.saveState(workflowId, state);
    await this.archiveWorkflow(workflowId);
    
    return state;
  }
  
  /**
   * Create a checkpoint
   */
  async createCheckpoint(workflowId, checkpointName) {
    const state = await this.getState(workflowId);
    if (!state) throw new Error(`Workflow ${workflowId} not found`);
    
    const checkpoint = {
      name: checkpointName,
      timestamp: new Date().toISOString(),
      state: JSON.parse(JSON.stringify(state))
    };
    
    state.checkpoints.push(checkpoint);
    await this.saveState(workflowId, state);
    
    return checkpoint;
  }
  
  /**
   * Restore from checkpoint
   */
  async restoreCheckpoint(workflowId, checkpointName) {
    const state = await this.getState(workflowId);
    if (!state) throw new Error(`Workflow ${workflowId} not found`);
    
    const checkpoint = state.checkpoints.find(cp => cp.name === checkpointName);
    if (!checkpoint) throw new Error(`Checkpoint ${checkpointName} not found`);
    
    const restoredState = {
      ...checkpoint.state,
      restoredFrom: checkpointName,
      restoredAt: new Date().toISOString()
    };
    
    await this.saveState(workflowId, restoredState);
    return restoredState;
  }
  
  /**
   * Get workflow state
   */
  async getWorkflowState(workflowId) {
    return await this.getState(workflowId);
  }
  
  /**
   * Get workflow history
   */
  async getWorkflowHistory(workflowId) {
    if (this.stateHistory.has(workflowId)) {
      return this.stateHistory.get(workflowId);
    }
    
    if (this.kvNamespace) {
      try {
        const history = await this.kvNamespace.get(`history:${workflowId}`, 'json');
        return history || [];
      } catch (error) {
        console.error('Failed to get workflow history:', error);
        return [];
      }
    }
    
    return [];
  }
  
  /**
   * List all workflows
   */
  async listWorkflows(options = {}) {
    const { status, limit = 100, cursor } = options;
    
    if (this.kvNamespace) {
      try {
        const list = await this.kvNamespace.list({
          prefix: 'workflow:',
          limit,
          cursor
        });
        
        const workflows = await Promise.all(
          list.keys.map(async key => {
            const state = await this.kvNamespace.get(key.name, 'json');
            return state;
          })
        );
        
        return status
          ? workflows.filter(w => w.status === status)
          : workflows;
      } catch (error) {
        console.error('Failed to list workflows:', error);
      }
    }
    
    // Fallback to in-memory state
    const workflows = Array.from(this.inMemoryState.values());
    return status
      ? workflows.filter(w => w.status === status)
      : workflows;
  }
  
  /**
   * Clean up old workflows
   */
  async cleanupOldWorkflows(olderThanDays = 7) {
    const cutoffDate = new Date();
    cutoffDate.setDate(cutoffDate.getDate() - olderThanDays);
    
    const workflows = await this.listWorkflows();
    let cleaned = 0;
    
    for (const workflow of workflows) {
      if (workflow.endTime && new Date(workflow.endTime) < cutoffDate) {
        await this.deleteWorkflow(workflow.workflowId);
        cleaned++;
      }
    }
    
    return cleaned;
  }
  
  /**
   * Get workflow statistics
   */
  async getStatistics() {
    const workflows = await this.listWorkflows();
    
    const stats = {
      total: workflows.length,
      byStatus: {},
      averageDuration: 0,
      successRate: 0,
      topErrors: []
    };
    
    let totalDuration = 0;
    let completedCount = 0;
    const errorCounts = {};
    
    for (const workflow of workflows) {
      // Count by status
      stats.byStatus[workflow.status] = (stats.byStatus[workflow.status] || 0) + 1;
      
      // Calculate average duration
      if (workflow.duration) {
        totalDuration += workflow.duration;
        completedCount++;
      }
      
      // Count errors
      if (workflow.errors) {
        for (const error of workflow.errors) {
          const key = error.error || 'Unknown error';
          errorCounts[key] = (errorCounts[key] || 0) + 1;
        }
      }
    }
    
    // Calculate statistics
    if (completedCount > 0) {
      stats.averageDuration = totalDuration / completedCount;
    }
    
    if (stats.total > 0) {
      stats.successRate = (stats.byStatus.completed || 0) / stats.total;
    }
    
    // Get top errors
    stats.topErrors = Object.entries(errorCounts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 5)
      .map(([error, count]) => ({ error, count }));
    
    return stats;
  }
  
  /**
   * Save state to storage
   */
  async saveState(workflowId, state) {
    // Save to in-memory cache
    this.inMemoryState.set(workflowId, state);
    
    // Track history
    if (!this.stateHistory.has(workflowId)) {
      this.stateHistory.set(workflowId, []);
    }
    this.stateHistory.get(workflowId).push({
      timestamp: new Date().toISOString(),
      state: JSON.parse(JSON.stringify(state))
    });
    
    // Persist to KV if available
    if (this.kvNamespace) {
      try {
        await this.kvNamespace.put(
          `workflow:${workflowId}`,
          JSON.stringify(state),
          {
            expirationTtl: 86400 * 30 // 30 days
          }
        );
      } catch (error) {
        console.error('Failed to persist state to KV:', error);
      }
    }
  }
  
  /**
   * Get state from storage
   */
  async getState(workflowId) {
    // Check in-memory cache first
    if (this.inMemoryState.has(workflowId)) {
      return this.inMemoryState.get(workflowId);
    }
    
    // Try to load from KV
    if (this.kvNamespace) {
      try {
        const state = await this.kvNamespace.get(`workflow:${workflowId}`, 'json');
        if (state) {
          this.inMemoryState.set(workflowId, state);
          return state;
        }
      } catch (error) {
        console.error('Failed to load state from KV:', error);
      }
    }
    
    return null;
  }
  
  /**
   * Archive completed workflow
   */
  async archiveWorkflow(workflowId) {
    if (this.kvNamespace) {
      try {
        const state = await this.getState(workflowId);
        const history = this.stateHistory.get(workflowId) || [];
        
        // Save to archive
        await this.kvNamespace.put(
          `archive:${workflowId}`,
          JSON.stringify({ state, history }),
          {
            expirationTtl: 86400 * 90 // 90 days
          }
        );
        
        // Save history
        await this.kvNamespace.put(
          `history:${workflowId}`,
          JSON.stringify(history),
          {
            expirationTtl: 86400 * 90 // 90 days
          }
        );
      } catch (error) {
        console.error('Failed to archive workflow:', error);
      }
    }
  }
  
  /**
   * Delete workflow
   */
  async deleteWorkflow(workflowId) {
    this.inMemoryState.delete(workflowId);
    this.stateHistory.delete(workflowId);
    
    if (this.kvNamespace) {
      try {
        await Promise.all([
          this.kvNamespace.delete(`workflow:${workflowId}`),
          this.kvNamespace.delete(`archive:${workflowId}`),
          this.kvNamespace.delete(`history:${workflowId}`)
        ]);
      } catch (error) {
        console.error('Failed to delete workflow:', error);
      }
    }
  }
  
  /**
   * Calculate duration in milliseconds
   */
  calculateDuration(startTime, endTime) {
    const start = new Date(startTime);
    const end = new Date(endTime);
    return end - start;
  }
}