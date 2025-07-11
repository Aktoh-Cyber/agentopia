/**
 * Tool Registry for Dynamic Agent Discovery and Routing
 * This can be stored in KV, D1, or configured as environment variables
 */

export class ToolRegistry {
  constructor(registryData) {
    this.tools = registryData.tools || [];
    this.routingRules = registryData.routingRules || [];
  }

  /**
   * Register a new tool/agent
   */
  registerTool(tool) {
    this.tools.push({
      id: tool.id,
      name: tool.name,
      description: tool.description,
      endpoint: tool.endpoint,
      mcpTool: tool.mcpTool,
      keywords: tool.keywords || [],
      patterns: tool.patterns || [],
      priority: tool.priority || 0
    });
  }

  /**
   * Find the best tool for a given question
   */
  findToolForQuestion(question) {
    const lowerQuestion = question.toLowerCase();
    const matches = [];

    for (const tool of this.tools) {
      let score = 0;
      
      // Check keywords
      for (const keyword of tool.keywords) {
        if (lowerQuestion.includes(keyword.toLowerCase())) {
          score += 1;
        }
      }
      
      // Check patterns (regex)
      for (const pattern of tool.patterns) {
        if (new RegExp(pattern, 'i').test(question)) {
          score += 2; // Patterns are more specific, higher weight
        }
      }
      
      if (score > 0) {
        matches.push({ tool, score: score + tool.priority });
      }
    }

    // Return highest scoring tool
    if (matches.length > 0) {
      matches.sort((a, b) => b.score - a.score);
      return matches[0].tool;
    }
    
    return null;
  }

  /**
   * Get all registered tools (for UI or debugging)
   */
  getAllTools() {
    return this.tools;
  }

  /**
   * Export as JSON for storage
   */
  toJSON() {
    return {
      tools: this.tools,
      routingRules: this.routingRules,
      version: "1.0"
    };
  }
}

// Example registry configuration
export const DEFAULT_REGISTRY = {
  tools: [
    {
      id: "judge",
      name: "Judge - Vulnerability & Compliance Expert",
      description: "Specialized in CVE analysis, compliance frameworks, and security assessments",
      endpoint: "https://judge.mindhive.tech",
      mcpTool: "judge_vulnerability_compliance",
      keywords: [
        "cve", "vulnerability", "vulnerabilities", "exploit", "patch",
        "cvss", "score", "severity", "critical", "high risk",
        "zero day", "0day", "buffer overflow", "sql injection",
        "xss", "cross-site", "csrf", "remote code execution", "rce",
        "compliance", "compliant", "regulation", "framework",
        "soc 2", "soc2", "iso 27001", "iso27001", "nist",
        "gdpr", "hipaa", "pci-dss", "pci dss", "pcidss",
        "audit", "control", "requirement", "certification",
        "sox", "sarbanes", "fedramp", "ccpa", "privacy"
      ],
      patterns: [
        "CVE-\\d{4}-\\d+",
        "\\b(SOC\\s*2|GDPR|HIPAA|PCI[- ]?DSS)\\b",
        "compliance.*(requirement|audit|framework)"
      ],
      priority: 10
    }
    // Add more tools here as they're created
  ],
  routingRules: [
    {
      name: "vulnerability-first",
      description: "Route vulnerability questions to Judge first",
      condition: "contains_keyword",
      keywords: ["vulnerability", "cve"],
      action: "route_to_tool",
      toolId: "judge"
    }
  ]
};

/**
 * MCPClient with dynamic tool support
 */
export class DynamicMCPClient {
  constructor(registry) {
    this.registry = registry;
  }

  async askTool(question) {
    // Find appropriate tool
    const tool = this.registry.findToolForQuestion(question);
    
    if (!tool) {
      return null; // No specialized tool found
    }

    try {
      const response = await fetch(`${tool.endpoint}/mcp`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          method: 'tools/call',
          params: {
            name: tool.mcpTool,
            arguments: { question }
          }
        })
      });

      if (!response.ok) {
        throw new Error(`MCP request failed: ${response.status}`);
      }

      const result = await response.json();
      
      if (result.error) {
        throw new Error(`MCP error: ${result.error.message}`);
      }

      // Extract text content from MCP response
      if (result.content && result.content.length > 0 && result.content[0].type === 'text') {
        return {
          answer: result.content[0].text,
          source: tool.name,
          toolId: tool.id
        };
      }
      
      throw new Error('Unexpected response format');
    } catch (error) {
      console.error(`Error calling tool ${tool.id}:`, error);
      throw error;
    }
  }
}