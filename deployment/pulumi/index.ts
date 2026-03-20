import * as pulumi from "@pulumi/pulumi";
import * as cloudflare from "@pulumi/cloudflare";
import * as fs from "fs";
import * as path from "path";

// Get configuration
const config = new pulumi.Config();
const accountId = config.requireSecret("accountId");
const zoneId = config.requireSecret("zoneId");

// Base domain configuration
const baseDomain = "aktohcyber.com";
const subDomain = "a";

// Agent configurations
const agents = [
  {
    name: "infosec",
    displayName: "InfoSec Supervisor",
    subdomain: "infosec",
    configFile: "infosec-supervisor.json",
    type: "supervisor"
  },
  {
    name: "judge",
    displayName: "Judge - Vulnerability & Compliance",
    subdomain: "judge", 
    configFile: "judge.json",
    type: "specialist"
  },
  {
    name: "lancer",
    displayName: "Lancer - Red Team & Penetration Testing",
    subdomain: "lancer",
    configFile: "lancer.json", 
    type: "specialist"
  },
  {
    name: "scout",
    displayName: "Scout - Discovery & Reconnaissance",
    subdomain: "scout",
    configFile: "scout.json",
    type: "specialist" 
  },
  {
    name: "shield",
    displayName: "Shield - Blue Team & Incident Response",
    subdomain: "shield",
    configFile: "shield.json",
    type: "specialist"
  }
];

// Create KV namespace for caching
const cacheNamespace = new cloudflare.WorkersKvNamespace("aktoh-cyber-cache", {
  accountId: accountId,
  title: "aktoh-cyber-infosec-cache"
});

// Function to create DNS record and Worker for each agent
function createAgent(agent: typeof agents[0]) {
  const fullDomain = `${agent.subdomain}.${subDomain}.${baseDomain}`;
  
  // Create DNS record
  const dnsRecord = new cloudflare.Record(`${agent.name}-dns`, {
    zoneId: zoneId,
    name: `${agent.subdomain}.${subDomain}`,
    value: fullDomain,
    type: "CNAME",
    proxied: true,
    ttl: 1
  });

  // Read agent configuration
  const configPath = path.join(__dirname, "..", "configs", agent.configFile);
  let agentConfig;
  
  try {
    const configContent = fs.readFileSync(configPath, "utf8");
    agentConfig = JSON.parse(configContent);
    
    // Update placeholders with actual values
    agentConfig.accountId = accountId;
    agentConfig.zoneId = zoneId;
    agentConfig.domain = fullDomain;
  } catch (error) {
    throw new Error(`Failed to read config file ${configPath}: ${error}`);
  }

  // Generate the worker script based on agent type
  let workerScript: string;
  
  if (agent.type === "supervisor") {
    workerScript = generateSupervisorScript(agentConfig);
  } else {
    workerScript = generateSpecialistScript(agentConfig);
  }

  // Create the Cloudflare Worker
  const worker = new cloudflare.WorkerScript(`${agent.name}-worker`, {
    accountId: accountId,
    name: agent.name,
    content: workerScript,
    module: true,
    compatibilityDate: "2024-01-01",
    kvNamespaceBindings: [{
      name: "CACHE",
      namespaceId: cacheNamespace.id
    }],
    plainTextBindings: [{
      name: "MAX_TOKENS",
      text: agentConfig.maxTokens.toString()
    }, {
      name: "TEMPERATURE", 
      text: agentConfig.temperature.toString()
    }],
    serviceBindings: [{
      name: "AI",
      service: "@cf/workers-ai",
      environment: "production"
    }]
  });

  // Create Worker route
  const route = new cloudflare.WorkerRoute(`${agent.name}-route`, {
    zoneId: zoneId,
    pattern: `${fullDomain}/*`,
    scriptName: worker.name
  });

  return {
    dns: dnsRecord,
    worker: worker,
    route: route,
    domain: fullDomain
  };
}

// Generate supervisor script
function generateSupervisorScript(config: any): string {
  return `
import { LangGraphAgent } from './langgraph-agent.js';

class ${config.name.replace(/[^a-zA-Z0-9]/g, '')}Agent extends LangGraphAgent {
  constructor() {
    super(${JSON.stringify(config, null, 2)});
  }
}

export default {
  async fetch(request, env) {
    const agent = new ${config.name.replace(/[^a-zA-Z0-9]/g, '')}Agent();
    return agent.fetch(request, env);
  }
};
  `.trim();
}

// Generate specialist script  
function generateSpecialistScript(config: any): string {
  return `
import { BaseAgent } from './base-agent.js';

class ${config.name.replace(/[^a-zA-Z0-9]/g, '')}Agent extends BaseAgent {
  constructor() {
    super(${JSON.stringify(config, null, 2)});
  }
}

export default {
  async fetch(request, env) {
    const agent = new ${config.name.replace(/[^a-zA-Z0-9]/g, '')}Agent();
    return agent.fetch(request, env);
  }
};
  `.trim();
}

// Deploy all agents
const deployedAgents = agents.map(agent => createAgent(agent));

// --- Synapse Controlplane DNS ---
// Points controlplane.aktohcyber.com to the horsemen-infra ALB
const infraStackName = config.get("infraStack") || "";
const synapseControlPlaneAlbDns = config.get("synapseControlPlaneAlbDns") || "";

if (synapseControlPlaneAlbDns) {
  const controlplaneDns = new cloudflare.Record("synapse-controlplane-dns", {
    zoneId: zoneId,
    name: "controlplane",
    content: synapseControlPlaneAlbDns,
    type: "CNAME",
    proxied: true,
    ttl: 1,
  });
}

// Export the deployed domains
export const deployedDomains = deployedAgents.map((agent, index) => ({
  name: agents[index].displayName,
  domain: agent.domain
}));

export const cacheNamespaceId = cacheNamespace.id;