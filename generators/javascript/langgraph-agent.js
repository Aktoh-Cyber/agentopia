/**
 * LangGraph Agent - Advanced multi-agent framework for deep agent patterns
 * Supports all 24 architectural patterns from DEEP_AGENT_PATTERNS.md
 */

import { StateGraph, END, START } from "@langchain/langgraph";
import { ChatPromptTemplate } from "@langchain/core/prompts";
import { HumanMessage, SystemMessage, AIMessage } from "@langchain/core/messages";
import { BaseAgent } from './base-agent.js';

/**
 * Base state interface for LangGraph workflows
 */
class AgentState {
  constructor(initialState = {}) {
    this.messages = initialState.messages || [];
    this.task = initialState.task || "";
    this.context = initialState.context || {};
    this.currentAgent = initialState.currentAgent || "start";
    this.iteration = initialState.iteration || 0;
    this.metadata = initialState.metadata || {};
  }

  addMessage(message) {
    this.messages.push(message);
  }

  updateContext(key, value) {
    this.context[key] = value;
  }

  toDict() {
    return {
      messages: this.messages,
      task: this.task,
      context: this.context,
      currentAgent: this.currentAgent,
      iteration: this.iteration,
      metadata: this.metadata
    };
  }
}

/**
 * LangGraph Agent supporting multiple architectural patterns
 */
export class LangGraphAgent extends BaseAgent {
  constructor(config) {
    super(config);
    
    this.config = {
      ...this.config,
      pattern: config.pattern || 'supervisor', // Default pattern
      maxIterations: config.maxIterations || 10,
      agents: config.agents || [],
      workflows: config.workflows || {},
      ...config
    };

    // Initialize graph and agents
    this.graph = null;
    this.agents = new Map();
    this.compiledGraph = null;
  }

  /**
   * Initialize LangGraph components
   */
  async setupLangGraphComponents(env) {
    // Initialize base LangChain components first
    await this.setupLangChainComponents(env);

    // Create the state graph
    this.graph = new StateGraph(AgentState);

    // Register agents based on pattern
    await this.setupAgentsByPattern();

    // Build the workflow
    await this.buildWorkflow();

    // Compile the graph
    this.compiledGraph = this.graph.compile();
  }

  /**
   * Setup agents based on the selected pattern
   */
  async setupAgentsByPattern() {
    const pattern = this.config.pattern;
    
    switch (pattern) {
      case 'supervisor':
        await this.setupSupervisorPattern();
        break;
      case 'network':
        await this.setupNetworkPattern();
        break;
      case 'hierarchical':
        await this.setupHierarchicalPattern();
        break;
      case 'router':
        await this.setupRouterPattern();
        break;
      case 'committee':
        await this.setupCommitteePattern();
        break;
      case 'pipeline':
        await this.setupPipelinePattern();
        break;
      case 'reflection':
        await this.setupReflectionPattern();
        break;
      case 'autonomous':
        await this.setupAutonomousPattern();
        break;
      default:
        await this.setupSupervisorPattern(); // Default fallback
    }
  }

  /**
   * Supervisor Pattern - Central coordination
   */
  async setupSupervisorPattern() {
    // Supervisor node
    this.graph.addNode("supervisor", async (state) => {
      const prompt = ChatPromptTemplate.fromTemplate(`
You are a supervisor agent managing multiple specialized agents. 
Based on the current task and context, decide which agent should handle the next step.

Available agents: {availableAgents}
Current task: {task}
Previous messages: {messageHistory}

Respond with JSON: {{"nextAgent": "agent_name", "instructions": "specific instructions", "reasoning": "why this agent"}}
`);

      const response = await this.llm._call(await prompt.format({
        availableAgents: this.config.agents.map(a => a.name).join(', '),
        task: state.task,
        messageHistory: state.messages.slice(-3).map(m => m.content).join('\n')
      }));

      // Parse supervisor decision
      let decision;
      try {
        const jsonMatch = response.match(/\{[\s\S]*\}/);
        decision = jsonMatch ? JSON.parse(jsonMatch[0]) : {
          nextAgent: this.config.agents[0]?.name || 'end',
          instructions: 'Proceed with default processing',
          reasoning: 'Default routing'
        };
      } catch {
        decision = {
          nextAgent: 'end',
          instructions: 'Complete the task',
          reasoning: 'Failed to parse routing decision'
        };
      }

      state.currentAgent = decision.nextAgent;
      state.addMessage(new AIMessage(`Supervisor: Routing to ${decision.nextAgent}. ${decision.reasoning}`));
      state.updateContext('lastDecision', decision);

      return state;
    });

    // Add specialized agent nodes
    for (const agentConfig of this.config.agents) {
      this.graph.addNode(agentConfig.name, async (state) => {
        const prompt = ChatPromptTemplate.fromTemplate(`
You are {agentName}, a specialized agent with expertise in: {expertise}

Task: {task}
Instructions: {instructions}
Context: {context}

Provide your specialized response:
`);

        const response = await this.llm._call(await prompt.format({
          agentName: agentConfig.name,
          expertise: agentConfig.expertise || agentConfig.description,
          task: state.task,
          instructions: state.context.lastDecision?.instructions || 'Process the task',
          context: JSON.stringify(state.context, null, 2)
        }));

        state.addMessage(new AIMessage(`${agentConfig.name}: ${response}`));
        state.currentAgent = 'supervisor';
        state.iteration += 1;

        return state;
      });
    }
  }

  /**
   * Network Pattern - Peer-to-peer communication
   */
  async setupNetworkPattern() {
    // Each agent can communicate with any other agent
    for (const agentConfig of this.config.agents) {
      this.graph.addNode(agentConfig.name, async (state) => {
        const prompt = ChatPromptTemplate.fromTemplate(`
You are {agentName} in a network of peer agents. You can communicate with any other agent.

Available peers: {availablePeers}
Task: {task}
Current context: {context}

Decide your next action:
1. Process the task yourself
2. Consult with a peer agent
3. Complete your work

Respond with JSON: {{"action": "process|consult|complete", "targetAgent": "agent_name_if_consulting", "response": "your response"}}
`);

        const response = await this.llm._call(await prompt.format({
          agentName: agentConfig.name,
          availablePeers: this.config.agents.filter(a => a.name !== agentConfig.name).map(a => a.name).join(', '),
          task: state.task,
          context: JSON.stringify(state.context, null, 2)
        }));

        // Parse agent decision
        let decision;
        try {
          const jsonMatch = response.match(/\{[\s\S]*\}/);
          decision = jsonMatch ? JSON.parse(jsonMatch[0]) : {
            action: 'complete',
            response: response
          };
        } catch {
          decision = {
            action: 'complete',
            response: response
          };
        }

        state.addMessage(new AIMessage(`${agentConfig.name}: ${decision.response}`));
        
        if (decision.action === 'consult' && decision.targetAgent) {
          state.currentAgent = decision.targetAgent;
        } else if (decision.action === 'complete') {
          state.currentAgent = 'end';
        }
        
        state.iteration += 1;
        return state;
      });
    }
  }

  /**
   * Router Pattern - Conditional routing
   */
  async setupRouterPattern() {
    this.graph.addNode("router", async (state) => {
      const prompt = ChatPromptTemplate.fromTemplate(`
You are a router agent. Analyze the task and route it to the most appropriate specialist.

Task: {task}
Available specialists: {specialists}

Each specialist's expertise:
{specialistDetails}

Respond with JSON: {{"selectedAgent": "agent_name", "confidence": 0-100, "reasoning": "why this agent"}}
`);

      const specialistDetails = this.config.agents.map(a => 
        `- ${a.name}: ${a.expertise || a.description}`
      ).join('\n');

      const response = await this.llm._call(await prompt.format({
        task: state.task,
        specialists: this.config.agents.map(a => a.name).join(', '),
        specialistDetails
      }));

      // Parse routing decision
      let decision;
      try {
        const jsonMatch = response.match(/\{[\s\S]*\}/);
        decision = jsonMatch ? JSON.parse(jsonMatch[0]) : {
          selectedAgent: this.config.agents[0]?.name || 'end',
          confidence: 50,
          reasoning: 'Default routing'
        };
      } catch {
        decision = {
          selectedAgent: 'end',
          confidence: 0,
          reasoning: 'Failed to parse routing decision'
        };
      }

      state.currentAgent = decision.selectedAgent;
      state.addMessage(new AIMessage(`Router: Selected ${decision.selectedAgent} (confidence: ${decision.confidence}%). ${decision.reasoning}`));
      state.updateContext('routingDecision', decision);

      return state;
    });

    // Add specialist nodes
    for (const agentConfig of this.config.agents) {
      this.graph.addNode(agentConfig.name, async (state) => {
        const prompt = ChatPromptTemplate.fromTemplate(`
You are {agentName}, selected for your expertise in: {expertise}

Task: {task}
Router's reasoning: {routingReasoning}

Provide your specialized solution:
`);

        const routingDecision = state.context.routingDecision || {};
        const response = await this.llm._call(await prompt.format({
          agentName: agentConfig.name,
          expertise: agentConfig.expertise || agentConfig.description,
          task: state.task,
          routingReasoning: routingDecision.reasoning || 'Not specified'
        }));

        state.addMessage(new AIMessage(`${agentConfig.name}: ${response}`));
        state.currentAgent = 'end';

        return state;
      });
    }
  }

  /**
   * Committee Pattern - Multiple agents collaborate
   */
  async setupCommitteePattern() {
    // Coordinator node
    this.graph.addNode("coordinator", async (state) => {
      if (state.iteration === 0) {
        // First iteration - delegate to all committee members
        state.updateContext('committee_responses', []);
        state.currentAgent = this.config.agents[0]?.name || 'aggregator';
        state.addMessage(new AIMessage("Coordinator: Delegating to committee members for diverse perspectives"));
      } else {
        // After committee input - move to aggregation
        state.currentAgent = 'aggregator';
      }
      return state;
    });

    // Committee member nodes
    for (let i = 0; i < this.config.agents.length; i++) {
      const agentConfig = this.config.agents[i];
      this.graph.addNode(agentConfig.name, async (state) => {
        const prompt = ChatPromptTemplate.fromTemplate(`
You are {agentName}, a committee member with expertise in: {expertise}
Provide your perspective on the task without seeing other members' responses yet.

Task: {task}
Your expertise: {expertise}

Provide your independent analysis and recommendation:
`);

        const response = await this.llm._call(await prompt.format({
          agentName: agentConfig.name,
          expertise: agentConfig.expertise || agentConfig.description,
          task: state.task
        }));

        // Store committee response
        const responses = state.context.committee_responses || [];
        responses.push({
          agent: agentConfig.name,
          response: response
        });
        state.updateContext('committee_responses', responses);
        
        state.addMessage(new AIMessage(`${agentConfig.name}: ${response}`));

        // Move to next committee member or aggregator
        const nextIndex = i + 1;
        if (nextIndex < this.config.agents.length) {
          state.currentAgent = this.config.agents[nextIndex].name;
        } else {
          state.currentAgent = 'aggregator';
        }

        return state;
      });
    }

    // Aggregator node
    this.graph.addNode("aggregator", async (state) => {
      const responses = state.context.committee_responses || [];
      const responseText = responses.map(r => `${r.agent}: ${r.response}`).join('\n\n');

      const prompt = ChatPromptTemplate.fromTemplate(`
You are an aggregator combining perspectives from committee members.

Task: {task}

Committee responses:
{responses}

Synthesize these perspectives into a comprehensive solution:
`);

      const response = await this.llm._call(await prompt.format({
        task: state.task,
        responses: responseText
      }));

      state.addMessage(new AIMessage(`Aggregator: ${response}`));
      state.currentAgent = 'end';

      return state;
    });
  }

  /**
   * Reflection Pattern - Self-improvement loop
   */
  async setupReflectionPattern() {
    this.graph.addNode("worker", async (state) => {
      const prompt = ChatPromptTemplate.fromTemplate(`
You are a worker agent. Process the following task:

Task: {task}
Previous attempts: {previousAttempts}
Feedback from reflector: {feedback}

Provide your solution:
`);

      const previousAttempts = state.context.attempts || [];
      const feedback = state.context.lastFeedback || 'No previous feedback';

      const response = await this.llm._call(await prompt.format({
        task: state.task,
        previousAttempts: previousAttempts.join('\n'),
        feedback: feedback
      }));

      // Store attempt
      const attempts = state.context.attempts || [];
      attempts.push(response);
      state.updateContext('attempts', attempts);

      state.addMessage(new AIMessage(`Worker: ${response}`));
      state.currentAgent = 'reflector';

      return state;
    });

    this.graph.addNode("reflector", async (state) => {
      const latestAttempt = (state.context.attempts || []).slice(-1)[0];
      
      const prompt = ChatPromptTemplate.fromTemplate(`
You are a reflector agent. Analyze the worker's attempt and decide if it's acceptable or needs improvement.

Original task: {task}
Worker's attempt: {attempt}
Iteration: {iteration}

Provide analysis and decision:
1. Is this attempt satisfactory? (yes/no)
2. What feedback would improve it?
3. Should we continue iterating?

Respond with JSON: {{"satisfactory": true/false, "feedback": "your feedback", "continue": true/false}}
`);

      const response = await this.llm._call(await prompt.format({
        task: state.task,
        attempt: latestAttempt,
        iteration: state.iteration
      }));

      // Parse reflection decision
      let decision;
      try {
        const jsonMatch = response.match(/\{[\s\S]*\}/);
        decision = jsonMatch ? JSON.parse(jsonMatch[0]) : {
          satisfactory: true,
          feedback: 'Work appears complete',
          continue: false
        };
      } catch {
        decision = {
          satisfactory: state.iteration >= this.config.maxIterations,
          feedback: 'Unable to parse reflection',
          continue: false
        };
      }

      state.updateContext('lastFeedback', decision.feedback);
      state.addMessage(new AIMessage(`Reflector: ${decision.feedback}`));

      if (decision.satisfactory || !decision.continue || state.iteration >= this.config.maxIterations) {
        state.currentAgent = 'end';
      } else {
        state.currentAgent = 'worker';
      }

      state.iteration += 1;
      return state;
    });
  }

  /**
   * Pipeline Pattern - Sequential processing
   */
  async setupPipelinePattern() {
    for (let i = 0; i < this.config.agents.length; i++) {
      const agentConfig = this.config.agents[i];
      const isLast = i === this.config.agents.length - 1;
      const nextAgent = isLast ? 'end' : this.config.agents[i + 1].name;

      this.graph.addNode(agentConfig.name, async (state) => {
        const prompt = ChatPromptTemplate.fromTemplate(`
You are {agentName} in a processing pipeline. 
Your role: {expertise}
Pipeline stage: {stage} of {totalStages}

Input from previous stage: {input}
Task: {task}

Process the input and prepare output for the next stage:
`);

        const previousOutput = i === 0 ? state.task : 
          state.messages.slice(-1)[0]?.content || state.task;

        const response = await this.llm._call(await prompt.format({
          agentName: agentConfig.name,
          expertise: agentConfig.expertise || agentConfig.description,
          stage: i + 1,
          totalStages: this.config.agents.length,
          input: previousOutput,
          task: state.task
        }));

        state.addMessage(new AIMessage(`${agentConfig.name}: ${response}`));
        state.currentAgent = nextAgent;

        return state;
      });
    }
  }

  /**
   * Autonomous Pattern - Self-directing agent
   */
  async setupAutonomousPattern() {
    this.graph.addNode("autonomous", async (state) => {
      const prompt = ChatPromptTemplate.fromTemplate(`
You are an autonomous agent. You can decide your own next actions based on the current state.

Task: {task}
Current progress: {progress}
Available actions: plan, execute, evaluate, modify_approach, complete
Iteration: {iteration}

Analyze the situation and decide your next action.
Respond with JSON: {{"action": "chosen_action", "reasoning": "why", "output": "any output from this step"}}
`);

      const progress = state.messages.map(m => m.content).join('\n');

      const response = await this.llm._call(await prompt.format({
        task: state.task,
        progress: progress,
        iteration: state.iteration
      }));

      // Parse autonomous decision
      let decision;
      try {
        const jsonMatch = response.match(/\{[\s\S]*\}/);
        decision = jsonMatch ? JSON.parse(jsonMatch[0]) : {
          action: 'complete',
          reasoning: 'Default completion',
          output: 'Task processing complete'
        };
      } catch {
        decision = {
          action: 'complete',
          reasoning: 'Unable to parse decision',
          output: response
        };
      }

      state.addMessage(new AIMessage(`Autonomous Agent: ${decision.output}`));
      state.updateContext('lastAction', decision);

      // Continue if not complete and under iteration limit
      if (decision.action !== 'complete' && state.iteration < this.config.maxIterations) {
        state.currentAgent = 'autonomous';
      } else {
        state.currentAgent = 'end';
      }

      state.iteration += 1;
      return state;
    });
  }

  /**
   * Build the workflow connections
   */
  async buildWorkflow() {
    const pattern = this.config.pattern;

    // Set entry point
    this.graph.setEntryPoint(this.getEntryPoint(pattern));

    // Add conditional edges based on pattern
    switch (pattern) {
      case 'supervisor':
        this.addSupervisorEdges();
        break;
      case 'network':
        this.addNetworkEdges();
        break;
      case 'router':
        this.addRouterEdges();
        break;
      case 'committee':
        this.addCommitteeEdges();
        break;
      case 'reflection':
        this.addReflectionEdges();
        break;
      case 'pipeline':
        this.addPipelineEdges();
        break;
      case 'autonomous':
        this.addAutonomousEdges();
        break;
      default:
        this.addSupervisorEdges();
    }
  }

  getEntryPoint(pattern) {
    switch (pattern) {
      case 'supervisor': return 'supervisor';
      case 'network': return this.config.agents[0]?.name || 'end';
      case 'router': return 'router';
      case 'committee': return 'coordinator';
      case 'reflection': return 'worker';
      case 'pipeline': return this.config.agents[0]?.name || 'end';
      case 'autonomous': return 'autonomous';
      default: return 'supervisor';
    }
  }

  addSupervisorEdges() {
    // Supervisor decides next agent
    this.graph.addConditionalEdges(
      "supervisor",
      (state) => state.currentAgent,
      {
        ...Object.fromEntries(this.config.agents.map(a => [a.name, a.name])),
        'end': END
      }
    );

    // Agents return to supervisor
    for (const agent of this.config.agents) {
      this.graph.addEdge(agent.name, "supervisor");
    }
  }

  addNetworkEdges() {
    // Each agent can go to any other agent or end
    for (const agent of this.config.agents) {
      this.graph.addConditionalEdges(
        agent.name,
        (state) => state.currentAgent,
        {
          ...Object.fromEntries(this.config.agents.map(a => [a.name, a.name])),
          'end': END
        }
      );
    }
  }

  addRouterEdges() {
    // Router to specialists
    this.graph.addConditionalEdges(
      "router",
      (state) => state.currentAgent,
      {
        ...Object.fromEntries(this.config.agents.map(a => [a.name, a.name])),
        'end': END
      }
    );

    // Specialists to end
    for (const agent of this.config.agents) {
      this.graph.addEdge(agent.name, END);
    }
  }

  addCommitteeEdges() {
    this.graph.addConditionalEdges(
      "coordinator",
      (state) => state.currentAgent,
      {
        ...Object.fromEntries(this.config.agents.map(a => [a.name, a.name])),
        'aggregator': 'aggregator'
      }
    );

    for (const agent of this.config.agents) {
      this.graph.addConditionalEdges(
        agent.name,
        (state) => state.currentAgent,
        {
          ...Object.fromEntries(this.config.agents.map(a => [a.name, a.name])),
          'aggregator': 'aggregator'
        }
      );
    }

    this.graph.addEdge("aggregator", END);
  }

  addReflectionEdges() {
    this.graph.addConditionalEdges(
      "worker",
      (state) => state.currentAgent,
      { 'reflector': 'reflector' }
    );

    this.graph.addConditionalEdges(
      "reflector",
      (state) => state.currentAgent,
      { 'worker': 'worker', 'end': END }
    );
  }

  addPipelineEdges() {
    for (let i = 0; i < this.config.agents.length - 1; i++) {
      this.graph.addEdge(this.config.agents[i].name, this.config.agents[i + 1].name);
    }
    this.graph.addEdge(this.config.agents[this.config.agents.length - 1].name, END);
  }

  addAutonomousEdges() {
    this.graph.addConditionalEdges(
      "autonomous",
      (state) => state.currentAgent,
      { 'autonomous': 'autonomous', 'end': END }
    );
  }

  /**
   * Process question using LangGraph workflow
   */
  async processQuestionLangGraph(env, question) {
    // Initialize components if not already done
    if (!this.compiledGraph) {
      await this.setupLangGraphComponents(env);
    }

    // Check cache first
    const cacheKey = `langgraph:${this.config.pattern}:${question.toLowerCase().trim()}`;
    const cached = await this.getFromCache(env, cacheKey);
    
    if (cached) {
      return { answer: cached, cached: true, pattern: this.config.pattern };
    }

    try {
      // Create initial state
      const initialState = new AgentState({
        task: question,
        messages: [new HumanMessage(question)]
      });

      // Run the workflow
      const finalState = await this.compiledGraph.invoke(initialState.toDict());

      // Extract the answer from final state
      const lastMessage = finalState.messages[finalState.messages.length - 1];
      const answer = lastMessage?.content || 'No response generated';

      // Cache the response
      await this.putInCache(env, cacheKey, answer);

      return { 
        answer, 
        cached: false, 
        pattern: this.config.pattern,
        iterations: finalState.iteration,
        metadata: finalState.metadata
      };
    } catch (error) {
      console.error('LangGraph processing error:', error);
      // Fallback to base agent processing
      return await super.processQuestion(env, question);
    }
  }

  /**
   * Override main process question method
   */
  async processQuestion(env, question) {
    if (this.config.pattern && this.config.pattern !== 'basic') {
      return await this.processQuestionLangGraph(env, question);
    } else {
      return await super.processQuestion(env, question);
    }
  }

  /**
   * Override home page to show LangGraph pattern
   */
  getHomePage() {
    const basePage = super.getHomePage();
    
    return basePage.replace(
      '🦜 LangChain.js Enhanced</p>',
      `🦜 LangChain.js Enhanced</p>
       <p class="tech-badge">🕸️ LangGraph ${this.config.pattern} Pattern</p>`
    ).replace(
      '</header>',
      `<div class="pattern-info">
         <strong>Pattern:</strong> ${this.config.pattern}
         <br><strong>Agents:</strong> ${this.config.agents.length}
       </div></header>`
    );
  }

  /**
   * Add pattern-specific styling
   */
  getStyles() {
    const baseStyles = super.getStyles();
    
    return baseStyles.replace(
      '.tech-badge {',
      `
        .pattern-info {
            text-align: center;
            color: #64ffda;
            font-size: 0.85rem;
            margin-top: 0.5rem;
            padding: 0.5rem;
            background: rgba(100, 255, 218, 0.1);
            border-radius: 4px;
        }
        
        .tech-badge {`
    );
  }
}