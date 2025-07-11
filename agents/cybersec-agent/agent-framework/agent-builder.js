/**
 * Agent Builder - Generates deployable agents from configuration
 */

import { validateConfig, getDefaultConfig } from './config-schema.js';

export class AgentBuilder {
  constructor() {
    this.templates = new Map();
    this.loadDefaultTemplates();
  }

  /**
   * Load default templates
   */
  loadDefaultTemplates() {
    // Router agent template
    this.templates.set('router', {
      indexTemplate: this.getRouterTemplate(),
      wranglerTemplate: this.getWranglerTemplate(),
      packageTemplate: this.getPackageTemplate(),
      deployScriptTemplate: this.getDeployScriptTemplate()
    });

    // Specialist agent template
    this.templates.set('specialist', {
      indexTemplate: this.getSpecialistTemplate(),
      wranglerTemplate: this.getWranglerTemplate(),
      packageTemplate: this.getPackageTemplate(),
      deployScriptTemplate: this.getDeployScriptTemplate()
    });
  }

  /**
   * Generate a new agent from configuration
   */
  async generateAgent(config, outputDir) {
    // Validate configuration
    const errors = validateConfig(config);
    if (errors.length > 0) {
      throw new Error(`Configuration validation failed: ${errors.join(', ')}`);
    }

    // Merge with defaults
    const fullConfig = {
      ...getDefaultConfig(config.type),
      ...config
    };

    // Get template
    const template = this.templates.get(config.type);
    if (!template) {
      throw new Error(`Unknown agent type: ${config.type}`);
    }

    // Generate files
    const files = {
      'src/index.js': this.processTemplate(template.indexTemplate, fullConfig),
      'wrangler.toml': this.processTemplate(template.wranglerTemplate, fullConfig),
      'package.json': this.processTemplate(template.packageTemplate, fullConfig),
      'scripts/deploy-all.sh': this.processTemplate(template.deployScriptTemplate, fullConfig),
      'README.md': this.generateReadme(fullConfig),
      '.env.local.example': this.generateEnvExample(),
      '.gitignore': this.generateGitignore()
    };

    return files;
  }

  /**
   * Process template with configuration substitution
   */
  processTemplate(template, config) {
    // Handle complex expressions like {{name.replace(/\s+/g, '')}}
    let result = template;
    
    // Simple replacements first
    result = result.replace(/\{\{(\w+(?:\.\w+)*)\}\}/g, (match, path) => {
      const value = this.getNestedValue(config, path);
      return value !== undefined ? value : match;
    });
    
    // Complex expressions - need to escape properly
    result = result.replace(/\{\{name\.replace\(\/\\?s\+\/g,\s*''\)\}\}/g, () => {
      if (!config.name) return 'Agent';
      // Create valid JavaScript identifier: remove spaces, hyphens, and other special chars
      return config.name.replace(/[^a-zA-Z0-9]/g, '');
    });
    
    result = result.replace(/\{\{JSON\.stringify\(examples\)\}\}/g, () => {
      return JSON.stringify(config.examples || []);
    });
    
    result = result.replace(/\{\{domain\.split\('\\.'\)\[0\]\}\}/g, () => {
      return config.domain ? config.domain.split('.')[0] : 'agent';
    });
    
    result = result.replace(/\{\{domain\.split\('\\.'\)\.slice\(1\)\.join\('\\.'\)\}\}/g, () => {
      return config.domain ? config.domain.split('.').slice(1).join('.') : 'example.com';
    });
    
    result = result.replace(/\{\{timestamp\}\}/g, () => {
      return config.timestamp || new Date().toISOString();
    });
    
    return result;
  }

  /**
   * Get nested value from object using dot notation
   */
  getNestedValue(obj, path) {
    return path.split('.').reduce((current, key) => current?.[key], obj);
  }

  /**
   * Router agent template
   */
  getRouterTemplate() {
    return `// Auto-generated router agent
// Generated from configuration at {{timestamp}}

import { BaseAgent } from '../agent-framework/base-agent.js';
import { ToolRegistry, DynamicMCPClient } from '../agent-framework/tool-registry.js';

class {{name.replace(/\s+/g, '')}}Agent extends BaseAgent {
  constructor() {
    super({
      name: '{{name}}',
      description: '{{description}}',
      icon: '{{icon}}',
      subtitle: '{{subtitle}}',
      systemPrompt: \`{{systemPrompt}}\`,
      placeholder: '{{placeholder}}',
      examples: {{JSON.stringify(examples)}},
      aiLabel: '{{aiLabel}}',
      footer: '{{footer}}',
      model: '{{model}}',
      maxTokens: {{maxTokens}},
      temperature: {{temperature}},
      cacheEnabled: {{cacheEnabled}},
      cacheTTL: {{cacheTTL}}
    });
    
    // Initialize tool registry
    this.registry = new ToolRegistry({{JSON.stringify(registry)}});
    this.mcpClient = new DynamicMCPClient(this.registry);
  }

  async processQuestion(env, question) {
    // Check cache first
    const cacheKey = \`q:\${question.toLowerCase().trim()}\`;
    const cached = await this.getFromCache(env, cacheKey);
    
    if (cached) {
      return { answer: cached, cached: true };
    }

    let answer;
    let source = this.config.name;

    // Try to route to specialized agent
    try {
      const toolResult = await this.mcpClient.askTool(question);
      
      if (toolResult) {
        answer = toolResult.answer;
        source = toolResult.source;
        
        // Add attribution
        answer = \`\${answer}\\n\\n*[This response was provided by \${source}]*\`;
      }
    } catch (error) {
      console.error('Failed to contact specialized agent:', error);
      // Fall through to local AI
    }

    // If no specialized agent or it failed, use local AI
    if (!answer) {
      const enhancedPrompt = \`\${this.config.systemPrompt}
      
Note: You have access to specialized agents for certain topics:
\${this.getToolSummary()}
If a question is better suited for a specialized agent, mention it in your response.\`;

      const response = await env.AI.run(this.config.model, {
        messages: [
          { role: 'system', content: enhancedPrompt },
          { role: 'user', content: \`Question: \${question}\` }
        ],
        max_tokens: this.config.maxTokens,
        temperature: this.config.temperature,
      });

      answer = response.response || 'I apologize, but I could not generate a response. Please try again.';
    }

    // Cache the response
    await this.putInCache(env, cacheKey, answer);

    return { answer, cached: false, source };
  }

  getToolSummary() {
    const tools = this.registry.getAllTools();
    if (tools.length === 0) {
      return 'No specialized agents currently available.';
    }

    return tools.map(tool => 
      \`- \${tool.name}: \${tool.description}\`
    ).join('\\n');
  }
}

// Export default handler
export default {
  async fetch(request, env) {
    const agent = new {{name.replace(/\s+/g, '')}}Agent();
    return agent.fetch(request, env);
  }
};`;
  }

  /**
   * Specialist agent template
   */
  getSpecialistTemplate() {
    return `// Auto-generated specialist agent
// Generated from configuration at {{timestamp}}

import { BaseAgent } from '../agent-framework/base-agent.js';

class {{name.replace(/\s+/g, '')}}Agent extends BaseAgent {
  constructor() {
    super({
      name: '{{name}}',
      description: '{{description}}',
      icon: '{{icon}}',
      subtitle: '{{subtitle}}',
      systemPrompt: \`{{systemPrompt}}\`,
      placeholder: '{{placeholder}}',
      examples: {{JSON.stringify(examples)}},
      aiLabel: '{{aiLabel}}',
      footer: '{{footer}}',
      model: '{{model}}',
      maxTokens: {{maxTokens}},
      temperature: {{temperature}},
      cacheEnabled: {{cacheEnabled}},
      cacheTTL: {{cacheTTL}},
      mcpToolName: '{{mcpToolName}}'
    });
  }

  // Specialist agents use the base processQuestion implementation
  // The specialized system prompt handles the domain expertise
}

// Export default handler
export default {
  async fetch(request, env) {
    const agent = new {{name.replace(/\s+/g, '')}}Agent();
    return agent.fetch(request, env);
  }
};`;
  }

  /**
   * Wrangler configuration template
   */
  getWranglerTemplate() {
    return `name = "{{domain.split('.')[0]}}"
main = "src/index.js"
compatibility_date = "2024-01-01"
account_id = "{{accountId}}"

[ai]
binding = "AI"

[[kv_namespaces]]
binding = "CACHE"
id = "94f2859d6efd4fc8830887d5d797324a"

[vars]
MAX_TOKENS = "{{maxTokens}}"
TEMPERATURE = "{{temperature}}"

[[routes]]
pattern = "{{domain}}/*"
zone_id = "{{zoneId}}"`;
  }

  /**
   * Package.json template
   */
  getPackageTemplate() {
    return `{
  "name": "{{domain.split('.')[0]}}",
  "version": "1.0.0",
  "description": "{{description}}",
  "main": "src/index.js",
  "scripts": {
    "dev": "wrangler dev",
    "deploy": "wrangler deploy"
  },
  "dependencies": {
    "wrangler": "^3.0.0"
  }
}`;
  }

  /**
   * Deployment script template
   */
  getDeployScriptTemplate() {
    return `#!/bin/bash

# Colors for output
RED='\\033[0;31m'
GREEN='\\033[0;32m'
YELLOW='\\033[1;33m'
NC='\\033[0m' # No Color

echo -e "\${YELLOW}{{name}} Deployment\${NC}"
echo "================================================"

# Check if CLOUDFLARE_API_TOKEN is set
if [ -z "$CLOUDFLARE_API_TOKEN" ]; then
    echo -e "\${RED}ERROR: CLOUDFLARE_API_TOKEN environment variable is required\${NC}"
    exit 1
fi

ACCOUNT_ID="{{accountId}}"
SCRIPT_NAME="{{domain.split('.')[0]}}"
ZONE_ID="{{zoneId}}"

# Step 1: Create DNS record
echo -e "\\n\${YELLOW}Step 1: Creating DNS record for {{domain}}...\${NC}"

DNS_DATA=$(cat <<EOF
{
  "type": "CNAME",
  "name": "{{domain.split('.')[0]}}",
  "content": "{{domain.split('.').slice(1).join('.')}}",
  "ttl": 1,
  "proxied": true
}
EOF
)

DNS_RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \\
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d "$DNS_DATA")

if echo "$DNS_RESPONSE" | grep -q '"success":true'; then
    echo -e "\${GREEN}✓ DNS record created successfully\${NC}"
elif echo "$DNS_RESPONSE" | grep -q "already exists"; then
    echo -e "\${GREEN}✓ DNS record already exists\${NC}"
else
    echo -e "\${RED}✗ Failed to create DNS record\${NC}"
    echo "$DNS_RESPONSE"
fi

# Step 2: Deploy Worker
echo -e "\\n\${YELLOW}Step 2: Deploying Worker to Cloudflare...\${NC}"

METADATA=$(cat <<EOF
{
  "main_module": "index.js",
  "compatibility_date": "2024-01-01",
  "bindings": [
    {
      "type": "ai",
      "name": "AI"
    },
    {
      "type": "kv_namespace",
      "name": "CACHE",
      "namespace_id": "94f2859d6efd4fc8830887d5d797324a"
    },
    {
      "type": "plain_text",
      "name": "MAX_TOKENS",
      "text": "{{maxTokens}}"
    },
    {
      "type": "plain_text",
      "name": "TEMPERATURE",
      "text": "{{temperature}}"
    }
  ]
}
EOF
)

WORKER_RESPONSE=$(curl -s -X PUT "https://api.cloudflare.com/client/v4/accounts/$ACCOUNT_ID/workers/scripts/$SCRIPT_NAME" \\
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \\
  -F "metadata=$METADATA;type=application/json" \\
  -F "index.js=@src/index.js;type=application/javascript+module")

if echo "$WORKER_RESPONSE" | grep -q '"success":true'; then
    echo -e "\${GREEN}✓ Worker deployed successfully\${NC}"
else
    echo -e "\${RED}✗ Failed to deploy Worker\${NC}"
    echo "$WORKER_RESPONSE"
    exit 1
fi

# Step 3: Create route
echo -e "\\n\${YELLOW}Step 3: Creating route for {{domain}}...\${NC}"

ROUTE_DATA=$(cat <<EOF
{
  "pattern": "{{domain}}/*",
  "script": "$SCRIPT_NAME"
}
EOF
)

ROUTE_RESPONSE=$(curl -s -X POST "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/workers/routes" \\
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \\
  -H "Content-Type: application/json" \\
  -d "$ROUTE_DATA")

if echo "$ROUTE_RESPONSE" | grep -q '"success":true'; then
    echo -e "\${GREEN}✓ Route created successfully\${NC}"
elif echo "$ROUTE_RESPONSE" | grep -q "already exists"; then
    echo -e "\${GREEN}✓ Route already exists\${NC}"
else
    echo -e "\${RED}✗ Failed to create route\${NC}"
    echo "$ROUTE_RESPONSE"
fi

# Final message
echo -e "\\n\${GREEN}================================================\${NC}"
echo -e "\${GREEN}Deployment complete!\${NC}"
echo -e "\${GREEN}================================================\${NC}"
echo ""
echo "Your agent is now available at:"
echo -e "\${YELLOW}https://{{domain}}\${NC}"`;
  }

  /**
   * Generate README.md
   */
  generateReadme(config) {
    return `# ${config.name}

${config.description}

🔗 **Live Demo**: https://${config.domain}

## Features

- 🤖 AI-powered responses using Cloudflare Workers AI
- ${config.type === 'router' ? '🔄 Intelligent routing to specialized agents' : '⚡ Specialized expertise'}
- 💾 Response caching for improved performance
- 🎨 Clean, professional web interface
- 📡 RESTful API endpoint
${config.type === 'specialist' ? '- 🔌 MCP server interface for agent-to-agent communication' : ''}

## Configuration

This agent was generated from configuration with the following settings:

- **Type**: ${config.type}
- **Model**: ${config.model}
- **Max Tokens**: ${config.maxTokens}
- **Temperature**: ${config.temperature}
- **Cache TTL**: ${config.cacheTTL} seconds
${config.type === 'router' ? `- **Registered Tools**: ${config.registry?.tools?.length || 0}` : ''}

## API Usage

### Web Interface
Visit https://${config.domain} to use the interactive chat interface.

### REST API Endpoint
\`\`\`bash
POST https://${config.domain}/api/ask
Content-Type: application/json

{
  "question": "Your question here"
}
\`\`\`

${config.type === 'specialist' ? `### MCP Interface
\`\`\`bash
POST https://${config.domain}/mcp
Content-Type: application/json

{
  "method": "tools/call",
  "params": {
    "name": "${config.mcpToolName || config.name.toLowerCase().replace(/\s+/g, '_')}_tool",
    "arguments": {
      "question": "Your question here"
    }
  }
}
\`\`\`` : ''}

## Deployment

1. Set up your Cloudflare API token:
   \`\`\`bash
   export CLOUDFLARE_API_TOKEN="your-token-here"
   \`\`\`

2. Run the deployment script:
   \`\`\`bash
   ./scripts/deploy-all.sh
   \`\`\`

## Example Questions

${config.examples?.map(ex => `- ${ex}`).join('\n') || '- Ask me anything!'}

---
*Generated by Agent Framework v1.0*`;
  }

  /**
   * Generate .env.local.example
   */
  generateEnvExample() {
    return `export CLOUDFLARE_API_TOKEN=your-api-token-here`;
  }

  /**
   * Generate .gitignore
   */
  generateGitignore() {
    return `node_modules/
.env.local
.env
*.log
.wrangler/
dist/`;
  }
}

/**
 * CLI function to build an agent
 */
export async function buildAgentFromFile(configPath, outputDir) {
  const fs = await import('fs/promises');
  const path = await import('path');
  
  // Read configuration
  const configContent = await fs.readFile(configPath, 'utf-8');
  const config = JSON.parse(configContent);
  
  // Add timestamp
  config.timestamp = new Date().toISOString();
  
  // Build agent
  const builder = new AgentBuilder();
  const files = await builder.generateAgent(config, outputDir);
  
  // Write files
  await fs.mkdir(outputDir, { recursive: true });
  
  for (const [filePath, content] of Object.entries(files)) {
    const fullPath = path.join(outputDir, filePath);
    const dir = path.dirname(fullPath);
    
    await fs.mkdir(dir, { recursive: true });
    await fs.writeFile(fullPath, content);
  }
  
  // Make scripts executable
  const scriptsDir = path.join(outputDir, 'scripts');
  try {
    const scripts = await fs.readdir(scriptsDir);
    for (const script of scripts) {
      if (script.endsWith('.sh')) {
        await fs.chmod(path.join(scriptsDir, script), '755');
      }
    }
  } catch (error) {
    // Scripts directory might not exist
  }
  
  console.log(`Agent generated successfully in ${outputDir}`);
  return files;
}