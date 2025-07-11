# Deployment and Testing Guide

This guide walks through deploying and testing the cybersec-agent and Judge integration.

## Architecture Overview

```
User Question → Cybersec-Agent → Judge (via MCP) → Specialized Response
                      ↓
                General Security Response (if not vulnerability/compliance)
```

## Deployment Process

### 1. Deploy Judge (Vulnerability & Compliance Expert)

```bash
cd judge/
source .env.local
./scripts/deploy-all.sh
```

**Expected Output**: Worker deployed successfully to https://judge.mindhive.tech

### 2. Deploy Cybersec-Agent (with Judge Integration)

```bash
cd cybersec-agent/
source .env.local
./scripts/deploy-all.sh
```

**Expected Output**: Worker deployed successfully to https://cybersec.mindhive.tech

## Validation Tests

### 1. Judge Standalone Tests

#### Test Web Interface
```bash
curl -s https://judge.mindhive.tech/ | head -20
```
**Expected**: HTML response with "Judge - Vulnerability & Compliance Expert" title

#### Test API Endpoint
```bash
curl -s -X POST https://judge.mindhive.tech/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is CVE-2021-44228?"}' | jq -r '.answer'
```
**Expected**: Detailed response about Log4Shell vulnerability

#### Test MCP Interface
```bash
# List available tools
curl -s -X POST https://judge.mindhive.tech/mcp \
  -H "Content-Type: application/json" \
  -d '{"method": "tools/list"}' | jq .

# Call vulnerability tool
curl -s -X POST https://judge.mindhive.tech/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "judge_vulnerability_compliance",
      "arguments": {
        "question": "What are SOC 2 requirements?"
      }
    }
  }' | jq -r '.content[0].text'
```
**Expected**: Tool list and detailed SOC 2 compliance response

### 2. Cybersec-Agent Integration Tests

#### Test General Security Questions (Local AI)
```bash
curl -s -X POST https://cybersec.mindhive.tech/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are basic network security practices?"}' | jq -r '.answer'
```
**Expected**: Response from local AI about network security

#### Test Vulnerability Questions (Should Route to Judge)
```bash
curl -s -X POST https://cybersec.mindhive.tech/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is CVE-2021-44228 vulnerability?"}' | jq -r '.answer'
```
**Expected**: Response ending with "*[This response was provided by Judge, our specialized vulnerability and compliance expert]*"

#### Test Compliance Questions (Should Route to Judge)
```bash
curl -s -X POST https://cybersec.mindhive.tech/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What are GDPR compliance requirements?"}' | jq -r '.answer'
```
**Expected**: Detailed compliance response (may or may not route to Judge depending on keyword matching)

## Keyword Routing Logic

The cybersec-agent routes questions to Judge based on these keywords:

### Vulnerability Keywords
- `cve`, `vulnerability`, `vulnerabilities`, `exploit`, `patch`
- `cvss`, `score`, `severity`, `critical`, `high risk`
- `zero day`, `0day`, `buffer overflow`, `sql injection`
- `xss`, `cross-site`, `csrf`, `remote code execution`, `rce`

### Compliance Keywords
- `compliance`, `compliant`, `regulation`, `framework`
- `soc 2`, `soc2`, `iso 27001`, `iso27001`, `nist`
- `gdpr`, `hipaa`, `pci-dss`, `pci dss`, `pcidss`
- `audit`, `control`, `requirement`, `certification`
- `sox`, `sarbanes`, `fedramp`, `ccpa`, `privacy`

## Testing Results Summary

✅ **Working Components**:
- Judge standalone web interface
- Judge API endpoint
- Judge MCP server interface
- Cybersec-agent general security questions
- Cybersec-agent routing for specific CVE questions
- Fallback to local AI when Judge unavailable

⚠️ **Partial/Variable Results**:
- Keyword matching sensitivity varies
- Some compliance questions route to Judge, others don't
- Response attribution format is consistent when routing occurs

## URLs

- **Judge**: https://judge.mindhive.tech
- **Cybersec-Agent**: https://cybersec.mindhive.tech

## Test Script

Use the automated test script for comprehensive validation:

```bash
./test-integration.sh
```

This script tests all major integration points and provides a quick health check.

## Troubleshooting

### Common Issues

1. **522 Errors**: DNS propagation delay (wait 5-10 minutes)
2. **Module Import Errors**: MCP client code is inlined to avoid ES module issues
3. **No Judge Attribution**: Check if question contains routing keywords
4. **Judge Unavailable**: Cybersec-agent falls back to local AI

### Debug Commands

```bash
# Check worker deployment status
curl -s "https://api.cloudflare.com/client/v4/accounts/82d842d586a0298981ab28617ec8ac66/workers/scripts" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" | jq -r '.result[] | .id'

# Check route configuration
curl -s "https://api.cloudflare.com/client/v4/zones/4f8b8a0bd742d7872f75b8144b3851f8/workers/routes" \
  -H "Authorization: Bearer $CLOUDFLARE_API_TOKEN" | jq -r '.result[]'
```

## Performance Notes

- **Judge Response Time**: ~2-3 seconds for complex queries
- **Cybersec-Agent Response Time**: ~1-2 seconds for local responses
- **MCP Overhead**: Minimal (~100ms for Judge routing)
- **Caching**: Both services use KV store for 1-hour cache

## Security Considerations

- All communication over HTTPS
- CORS enabled for web interface access
- No sensitive data logged
- Environment variables properly isolated
- MCP protocol uses standard JSON-RPC format

## Future Enhancements

1. Improve keyword detection accuracy
2. Add confidence scoring for routing decisions  
3. Implement circuit breaker for Judge failures
4. Add metrics and monitoring
5. Expand compliance framework coverage