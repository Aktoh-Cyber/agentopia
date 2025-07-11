// MCP Client for communicating with Judge service
export class MCPClient {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  async listTools() {
    const response = await fetch(`${this.baseUrl}/mcp`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        method: 'tools/list'
      })
    });

    if (!response.ok) {
      throw new Error(`MCP request failed: ${response.status}`);
    }

    return await response.json();
  }

  async callTool(toolName, args) {
    const response = await fetch(`${this.baseUrl}/mcp`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        method: 'tools/call',
        params: {
          name: toolName,
          arguments: args
        }
      })
    });

    if (!response.ok) {
      throw new Error(`MCP tool call failed: ${response.status}`);
    }

    const result = await response.json();
    
    if (result.error) {
      throw new Error(`MCP error: ${result.error.message}`);
    }

    return result;
  }

  async askJudge(question) {
    try {
      const result = await this.callTool('judge_vulnerability_compliance', { question });
      
      // Extract text content from MCP response format
      if (result.content && result.content.length > 0 && result.content[0].type === 'text') {
        return result.content[0].text;
      }
      
      throw new Error('Unexpected response format from Judge');
    } catch (error) {
      console.error('Error calling Judge:', error);
      throw error;
    }
  }
}

// Helper function to determine if a question should be routed to Judge
export function shouldAskJudge(question) {
  const lowerQuestion = question.toLowerCase();
  
  // Keywords that indicate vulnerability or compliance questions
  const vulnerabilityKeywords = [
    'cve', 'vulnerability', 'vulnerabilities', 'exploit', 'patch',
    'cvss', 'score', 'severity', 'critical', 'high risk',
    'zero day', '0day', 'buffer overflow', 'sql injection',
    'xss', 'cross-site', 'csrf', 'remote code execution', 'rce'
  ];
  
  const complianceKeywords = [
    'compliance', 'compliant', 'regulation', 'framework',
    'soc 2', 'soc2', 'iso 27001', 'iso27001', 'nist',
    'gdpr', 'hipaa', 'pci-dss', 'pci dss', 'pcidss',
    'audit', 'control', 'requirement', 'certification',
    'sox', 'sarbanes', 'fedramp', 'ccpa', 'privacy'
  ];
  
  // Check if question contains vulnerability or compliance keywords
  const hasVulnerabilityKeyword = vulnerabilityKeywords.some(keyword => 
    lowerQuestion.includes(keyword)
  );
  
  const hasComplianceKeyword = complianceKeywords.some(keyword => 
    lowerQuestion.includes(keyword)
  );
  
  return hasVulnerabilityKeyword || hasComplianceKeyword;
}