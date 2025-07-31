# Cloudflare Deployment Guide - Aktoh Cyber InfoSec Agents

This guide walks you through deploying the InfoSec LangGraph agents to Cloudflare using Pulumi infrastructure-as-code.

## 🎯 Overview

We'll be deploying:
- **InfoSec Supervisor Agent** at `infosec.a.aktohcyber.com`
- **Judge Agent** at `judge.a.aktohcyber.com`
- **Lancer Agent** at `lancer.a.aktohcyber.com`
- **Scout Agent** at `scout.a.aktohcyber.com`
- **Shield Agent** at `shield.a.aktohcyber.com`

## 📋 Prerequisites

### 1. Domain Setup
- You own `aktohcyber.com`
- Domain is configured in Cloudflare (DNS management)

### 2. Required Tools
```bash
# Install Pulumi
curl -fsSL https://get.pulumi.com | sh

# Install Node.js (for Pulumi TypeScript)
# Download from https://nodejs.org/ or use your package manager

# Install Wrangler CLI
npm install -g wrangler
```

### 3. Cloudflare Credentials
You'll need:
- **Cloudflare API Token** (with Workers and Zone permissions)
- **Account ID** 
- **Zone ID** for `aktohcyber.com`

To find these:
1. Go to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. **Account ID**: Right sidebar on any page
3. **Zone ID**: Domain overview page, right sidebar
4. **API Token**: My Profile → API Tokens → Create Token

## 🏗️ Infrastructure Setup

### Step 1: Get Your Cloudflare Information

First, let's gather the required information:

```bash
# Test your API token
export CLOUDFLARE_API_TOKEN="your-api-token-here"
curl -X GET "https://api.cloudflare.com/client/v4/user/tokens/verify" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json"
```

### Step 2: Find Your Zone and Account IDs

```bash
# List zones to find aktohcyber.com zone ID
curl -X GET "https://api.cloudflare.com/client/v4/zones" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" \
  -H "Content-Type: application/json" | jq '.result[] | select(.name=="aktohcyber.com") | {name, id, account_id: .account.id}'
```

## 🗂️ Project Structure

Let's create the deployment structure:

```
agentopia/
├── deployment/
│   ├── pulumi/
│   │   ├── Pulumi.yaml
│   │   ├── index.ts
│   │   ├── package.json
│   │   └── agents/
│   │       ├── infosec-supervisor.ts
│   │       ├── judge.ts
│   │       ├── lancer.ts
│   │       ├── scout.ts
│   │       └── shield.ts
│   └── configs/
│       ├── infosec-supervisor.json
│       ├── judge.json
│       ├── lancer.json
│       ├── scout.json
│       └── shield.json
```

## 🚀 Deployment Steps

### Step 3: Set Environment Variables

Set your Cloudflare credentials:

```bash
# Set your API token (keep this secure!)
export CLOUDFLARE_API_TOKEN="your-api-token-here"

# Set your Account ID (from Step 2)
export CLOUDFLARE_ACCOUNT_ID="your-account-id-here"

# Set your Zone ID for aktohcyber.com (from Step 2)
export CLOUDFLARE_ZONE_ID="your-zone-id-here"
```

### Step 4: Run the Deployment

The deployment structure has been created for you. Simply run:

```bash
# Navigate to the agentopia directory
cd /path/to/agentopia

# Run the deployment script
./deployment/deploy.sh
```

This script will:
1. ✅ Check all prerequisites
2. 📦 Install Pulumi dependencies
3. 🔧 Configure the Pulumi stack
4. 👀 Show you a preview of what will be deployed
5. 🚀 Deploy all 5 agents to Cloudflare
6. 🌐 Set up DNS records for `*.a.aktohcyber.com`

### Step 5: Verify Deployment

After deployment, test each agent:

```bash
# Test the InfoSec Supervisor
curl https://infosec.a.aktohcyber.com/

# Test Judge (Vulnerability & Compliance)
curl https://judge.a.aktohcyber.com/

# Test Lancer (Red Team & Penetration Testing)
curl https://lancer.a.aktohcyber.com/

# Test Scout (Discovery & Reconnaissance)
curl https://scout.a.aktohcyber.com/

# Test Shield (Blue Team & Incident Response)
curl https://shield.a.aktohcyber.com/
```

## 🔧 Configuration Details

### DNS Structure

All agents are deployed under the `a.aktohcyber.com` subdomain:

- `infosec.a.aktohcyber.com` - Main supervisor agent
- `judge.a.aktohcyber.com` - Vulnerability & compliance specialist
- `lancer.a.aktohcyber.com` - Red team & penetration testing specialist
- `scout.a.aktohcyber.com` - Discovery & reconnaissance specialist
- `shield.a.aktohcyber.com` - Blue team & incident response specialist

### Agent Capabilities

#### InfoSec Supervisor 🛡️
- **LangGraph Supervisor Pattern**: Intelligently routes questions to specialists
- **4 Specialized Agents**: Coordinates Judge, Lancer, Scout, and Shield
- **Smart Routing**: AI-powered decision making for optimal specialist selection

#### Judge ⚖️ (Vulnerability & Compliance)
- CVE analysis and CVSS scoring
- Compliance frameworks (SOC 2, GDPR, HIPAA, PCI-DSS, ISO 27001, NIST)
- Vulnerability scanning and assessment
- Risk assessment and gap analysis

#### Lancer ⚔️ (Red Team & Penetration Testing)
- Penetration testing methodologies (OWASP, NIST, PTES)
- Exploit development and payload creation
- Social engineering and phishing campaigns
- Red team operations and adversary simulation

#### Scout 🔍 (Discovery & Reconnaissance)
- Network mapping and port scanning (Nmap, Masscan)
- Service enumeration and banner grabbing
- OSINT techniques and passive reconnaissance
- Asset discovery and inventory management

#### Shield 🛡️ (Blue Team & Incident Response)
- Incident response procedures and playbooks
- Threat hunting methodologies and techniques
- SIEM rule development and tuning
- Digital forensics and SOC operations

## 🛠️ Troubleshooting

### Common Issues

1. **API Token Permissions**: Ensure your token has Zone and Workers permissions
2. **Domain Not in Cloudflare**: Make sure `aktohcyber.com` is managed by Cloudflare
3. **Pulumi Stack Issues**: Delete and recreate with `pulumi stack rm dev` then `pulumi stack init dev`

### Getting Help

If you encounter issues:
1. Check the Pulumi logs: `pulumi logs`
2. Verify Cloudflare dashboard shows the workers and DNS records
3. Test individual components with `curl` commands above

## 📚 Next Steps

After successful deployment:
1. 🔐 Set up monitoring and alerting
2. 📊 Configure analytics and logging
3. 🔄 Set up CI/CD for updates
4. 📖 Update internal documentation with new URLs
5. 🧪 Conduct security testing of the deployed agents

---

**🎉 Congratulations!** Your Aktoh Cyber InfoSec agents are now deployed and ready to assist with comprehensive security guidance!