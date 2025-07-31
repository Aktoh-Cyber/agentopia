Below is a comprehensive list of multi-agent (and related cognitive) architecture patterns that can be designed using LangGraph. Each pattern is summarized briefly and includes a Mermaid diagram to illustrate the structure. Many of these patterns can be mixed and matched, or extended, based on the needs of your application.

---

## 1. Network Architecture

Description  
All agents can communicate with every other agent, enabling fully connected, peer-to-peer interactions. Each agent decides who to call next based on the context.

Use Case

- Great for loosely structured collaboration where any agent may need to consult any other.
    
- Suited for scenarios without a clear hierarchy or sequence.
    

Diagram

graph LR

   A[Agent A] <--> B[Agent B]

   A <--> C[Agent C]

   B <--> C

  

---

## 2. Supervisor Architecture

Description  
A central “supervisor” agent orchestrates all tasks, delegating work to subordinate agents. The supervisor oversees state and determines the next step.

Use Case

- Ideal for tight control and coordination of tasks.
    
- Ensures each agent receives tasks only when appropriate.
    

Diagram

graph LR

    S[Supervisor] --> A[Agent A]

    S --> B[Agent B]

    S --> C[Agent C]

  

---

## 3. Supervisor (Tool-Calling) Architecture

Description  
A specialized supervisor that treats each agent as a “tool.” A tool-calling language model decides which subordinate “tool” to invoke, with what parameters, and in what order.

Use Case

- Best when agents behave like individual functions or services.
    
- Useful for dynamic invocation and parameterization of agents.
    

Diagram

graph LR

   S[Supervisor] --> |Invoke as tool| A[Agent A]

   S --> |Invoke as tool| B[Agent B]

   S --> |Invoke as tool| C[Agent C]

  

---

## 4. Hierarchical Architecture

Description  
Multiple layers of supervision. Top-level supervisors manage mid-level supervisors, who in turn direct the individual agent workers.

Use Case

- Useful for large systems divided into sub-domains or sub-tasks.
    
- Supports layered oversight and complexity management.
    

Diagram

graph LR

   Top[Top-Level Supervisor] --> Mid1[Mid-Level Supervisor 1]

   Top --> Mid2[Mid-Level Supervisor 2]

   Mid1 --> A[Agent A]

   Mid1 --> B[Agent B]

   Mid2 --> C[Agent C]

   Mid2 --> D[Agent D]

  

---

## 5. Custom Multi-Agent Workflow

Description  
Agents have selective and potentially conditional communication channels. Certain paths might be predefined, while others are chosen at runtime.

Use Case

- Best for specialized applications or partial automation scenarios.
    
- Offers both predictability (fixed paths) and adaptability (dynamic decisions).
    

Diagram

graph LR

   A[Agent A] --> |Conditional| B[Agent B]

   B --> C[Agent C]

   A --> D[Agent D]

   D --> B

  

---

## 6. Router Agent

Description  
A router agent dispatches tasks to one among multiple agents or sub-processes based on some decision logic, often using structured outputs to ensure clarity.

Use Case

- Useful for branching workflows where specific conditions dictate which agent to use.
    
- Common in classification or routing tasks.
    

Diagram

graph LR

   R[Router Agent] --> |Option1| A[Agent A]

   R --> |Option2| B[Agent B]

   R --> |Option3| C[Agent C]

  

---

## 7. Tool-Calling Agent

Description  
An agent capable of selecting and using multiple “tools” (which can be other agents, APIs, or functions). Often equipped with planning and memory to handle multi-step processes.

Use Case

- Suitable for dynamic problem-solving where external resources need to be called on-demand.
    
- Common in advanced LLM-driven workflows.
    

Diagram

graph LR

   T[Tool-Calling Agent] --> |calls| Tool1[Tool 1]

   T --> |calls| Tool2[Tool 2]

   T --> |calls| Tool3[Tool 3]

  

---

## 8. Human-in-the-Loop

Description  
Humans participate directly in the loop, providing oversight, approvals, or feedback. The human can guide or correct agent actions before final outputs are produced.

Use Case

- Critical for high-stakes or sensitive tasks requiring human judgment.
    
- Useful for continuous improvement and quality control.
    

Diagram

graph LR

   U[User] --> H[Human Overseer]

   H --> A[Agent]

   A --> H

   H --> O[Final Output]

  

---

## 9. Parallelization

Description  
Multiple agents or tasks run concurrently. Once all parallel tasks complete, their results are combined or used for subsequent steps.

Use Case

- Ideal when work can be split into independent subtasks, significantly speeding up processing.
    
- Common in data processing or distributed computation.
    

Diagram

graph LR

   S[Start] --> A[Agent A]

   S --> B[Agent B]

   S --> C[Agent C]

   A --> End

   B --> End

   C --> End

  

---

## 10. Subgraphs

Description  
A system can be broken into smaller, self-contained subgraphs. Each subgraph handles a portion of the workflow or domain, then interfaces with others.

Use Case

- Useful for modularizing large systems.
    
- Simplifies development, testing, and maintenance.
    

Diagram

graph LR

   subgraph Subgraph1

   A[Agent A]

   B[Agent B]

   end

   subgraph Subgraph2

   C[Agent C]

   D[Agent D]

   end

  

   A --> C

   B --> D

  

---

## 11. Reflection

Description  
Incorporates a feedback loop that allows agents to review and refine their performance. The agent can critique its outputs and update its approach iteratively.

Use Case

- Ideal for tasks needing continuous learning or iterative improvement.
    
- Allows for self-evaluation and adjustment within an agent.
    

Diagram

graph LR

   A[Agent] --> R[Reflection Process]

   R --> A

  

---

## 12. Single LLM Call (Cognitive Architecture)

Description  
The simplest cognitive architecture: user input goes to a single LLM call, and the response is immediately returned.

Use Case

- Best for straightforward Q&A or single-step tasks.
    
- Minimal overhead, quick to implement.
    

Diagram

graph LR

   U[User Input] --> LLM

   LLM --> O[Output]

  

---

## 13. Chain of LLM Calls (Cognitive Architecture)

Description  
Multiple LLM calls are chained sequentially. Each LLM invocation transforms or refines the output from the previous step.

Use Case

- Useful for more complex tasks that can be divided into distinct phases, such as extraction → analysis → summarization.
    

Diagram

graph LR

   U[User Input] --> LLM1

   LLM1 --> LLM2

   LLM2 --> O[Output]

  

---

## 14. Router (Cognitive Architecture)

Description  
The LLM decides which action, tool, or workflow to take next. This introduces branching logic and conditional decision-making in the chain.

Use Case

- Useful when tasks require dynamic selection of the next step based on user input or context.
    
- Overlaps with the “Router Agent” concept in multi-agent systems.
    

Diagram

graph LR

   U[User Input] --> R[Router]

   R --> |Path1| A[Action A]

   R --> |Path2| B[Action B]

  

---

## 15. State Machine (Cognitive Architecture)

Description  
A combination of LLM-driven decision-making and iterative loops. Each state leads to the next, possibly looping back if additional processing is needed.

Use Case

- Ideal for more elaborate processes where multiple iterations or checks are required.
    
- Often found in dialog systems or iterative refinement tasks.
    

Diagram

graph LR

   S[State] --> |LLM decides next state| S2[State 2]

   S2 --> |LLM decides next state| S3[State 3]

   S3 --> |Loop back or end| S

  

---

## 16. Autonomous Agent (Cognitive Architecture)

Description  
The system autonomously decides its own next steps. It may modify its prompts, call various tools, or even update its code/plans as needed.

Use Case

- Perfect for open-ended tasks where the agent must adapt to new information.
    
- Powers advanced “auto-LLM” workflows.
    

Diagram

graph LR

   U[User Input] --> A[Autonomous Agent]

   A --> A

   A --> O[Output]

  

---

## 17. Committee (Ensemble) Architecture

Description  
A coordinating agent (or aggregator) solicits multiple agents for their solutions or opinions. It then merges or chooses from among the responses to produce a final result.

Use Case

- Useful when you want diverse approaches or “opinions.”
    
- Helpful for tasks where combining multiple perspectives leads to better outcomes.
    

Diagram

graph LR

   U[User] --> C[Coordinator]

   C --> A[Agent A]

   C --> B[Agent B]

   C --> D[Agent C]

   A --> C

   B --> C

   D --> C

   C --> O[Combined Output]

  

---

## 18. Consultant Architecture

Description  
One primary agent consults with multiple specialized “expert” agents. The primary agent synthesizes insights from the experts and returns a result.

Use Case

- Use when one agent is the main decision-maker but needs targeted expertise from others.
    
- Simplifies the top-level logic while allowing for specialized analysis.
    

Diagram

graph LR

   U[User] --> P[Primary Agent]

   P --> E1[Expert Agent 1]

   P --> E2[Expert Agent 2]

   E1 --> P

   E2 --> P

   P --> O[Solution]

  

---

## 19. Pub-Sub Architecture

Description  
Agents subscribe to specific topics or events. A publisher agent emits messages that automatically route to all subscribers of that topic.

Use Case

- Useful when multiple agents need to react to certain types of updates without explicit direct calls.
    
- Common in event-driven or real-time systems.
    

Diagram

graph LR

   Pub[Publisher] --> TopicA((Topic A))

   Sub1[Subscriber 1] --> TopicA

   Sub2[Subscriber 2] --> TopicA

  

---

## 20. Pipeline Architecture

Description  
Agents form a linear workflow, where each agent’s output is the next agent’s input. Often used for sequential data processing stages.

Use Case

- Ideal for scenarios like data cleaning → feature extraction → analysis → reporting.
    
- Straightforward to implement and reason about.
    

Diagram

graph LR

   A[Agent A] --> B[Agent B]

   B --> C[Agent C]

   C --> D[Agent D]

  

---

## 21. Federated Architecture

Description  
Multiple domain-specialized agents operate in parallel, each handling a portion of the task or data. A global orchestrator collects and merges their outputs.

Use Case

- Useful when different models or experts handle distinct domains.
    
- Facilitates horizontal scalability and modular design.
    

Diagram

graph LR

   U[User Input] --> G[Global Orchestrator]

   G --> D1[Domain Expert 1]

   G --> D2[Domain Expert 2]

   G --> D3[Domain Expert 3]

   D1 --> G

   D2 --> G

   D3 --> G

   G --> O[Aggregate Output]

  

---

## 22. Voting-Based Aggregator Architecture

Description  
Multiple agents each produce an answer or recommendation. A voting mechanism (majority, weighted, or otherwise) decides the final answer.

Use Case

- Useful to reduce bias or single-agent errors by consulting multiple perspectives.
    
- Common in ensemble learning or group decision-making.
    

Diagram

graph LR

   U[User] --> Agg[Aggregator]

   Agg --> A[Agent 1]

   Agg --> B[Agent 2]

   Agg --> C[Agent 3]

   A --> Agg

   B --> Agg

   C --> Agg

   Agg --> O[Majority Vote]

  

---

## 23. Auction-Based Architecture

Description  
A central environment or orchestrator announces tasks. Agents “bid” or propose solutions, and the orchestrator assigns the task to the best bidder.

Use Case

- Useful when you need to pick the most cost-effective or highest-quality solution among many.
    
- Inspired by market-based multi-agent systems.
    

Diagram

graph LR

   Env[Marketplace] --> A[Agent 1]

   Env --> B[Agent 2]

   Env --> C[Agent 3]

   A --> Env

   B --> Env

   C --> Env

  

---

## 24. Swarm Architecture

Description  
Agents form a network where each communicates primarily with local neighbors. Through iterative local interactions, the group converges on a global solution.

Use Case

- Useful for distributed optimization or collective intelligence tasks.
    
- Common in swarm robotics or evolutionary algorithms.
    

Diagram

graph LR

   A[Agent 1] <--> B[Agent 2]

   B <--> C[Agent 3]

   C <--> A

  

---

## References

- [LangGraph Multi-Agent Concepts](https://langchain-ai.github.io/langgraph/concepts/multi_agent/?utm_source=chatgpt.com)
    
- [LangGraph Agentic Concepts](https://langchain-ai.github.io/langgraph/concepts/agentic_concepts/?utm_source=chatgpt.com)
    
- What is a "cognitive architecture"? (Discusses Single LLM Call, Chain of LLM Calls, Router, State Machine, Autonomous Agent)
    

---

By mixing and matching these patterns—or layering them—you can design sophisticated multi-agent systems tailored to your application’s needs. Whether you need a simple pipeline or a complex, hierarchical network of autonomous agents, LangGraph provides the flexibility to implement these diverse architectural styles.
