#!/bin/bash

echo "🧪 Testing Judge Integration"
echo "================================"

echo ""
echo "1. Testing Judge directly..."
JUDGE_RESPONSE=$(curl -s -X POST https://judge.mindhive.tech/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is CVE-2021-44228?"}')

echo "Judge Response Length: $(echo "$JUDGE_RESPONSE" | jq -r '.answer' | wc -c)"
echo "Judge Response Preview: $(echo "$JUDGE_RESPONSE" | jq -r '.answer' | head -c 100)..."

echo ""
echo "2. Testing Judge MCP endpoint..."
MCP_RESPONSE=$(curl -s -X POST https://judge.mindhive.tech/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "method": "tools/call",
    "params": {
      "name": "judge_vulnerability_compliance",
      "arguments": {
        "question": "What is CVE-2021-44228?"
      }
    }
  }')

echo "MCP Response: $(echo "$MCP_RESPONSE" | jq -c .)"

echo ""
echo "3. Testing Cybersec-Agent with vulnerability keyword..."
CYBERSEC_RESPONSE=$(curl -s -X POST https://cybersec.mindhive.tech/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "What is CVE-2021-44228 vulnerability?"}')

echo "Cybersec Response Length: $(echo "$CYBERSEC_RESPONSE" | jq -r '.answer' | wc -c)"
echo "Contains Judge Attribution: $(echo "$CYBERSEC_RESPONSE" | jq -r '.answer' | grep -c 'Judge' || echo '0')"
echo "Cybersec Response Preview: $(echo "$CYBERSEC_RESPONSE" | jq -r '.answer' | head -c 150)..."

echo ""
echo "4. Testing with compliance keyword..."
COMPLIANCE_RESPONSE=$(curl -s -X POST https://cybersec.mindhive.tech/api/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "SOC 2 compliance requirements"}')

echo "Compliance Response Length: $(echo "$COMPLIANCE_RESPONSE" | jq -r '.answer' | wc -c)"
echo "Contains Judge Attribution: $(echo "$COMPLIANCE_RESPONSE" | jq -r '.answer' | grep -c 'Judge' || echo '0')"
echo "Compliance Response Preview: $(echo "$COMPLIANCE_RESPONSE" | jq -r '.answer' | head -c 150)..."

echo ""
echo "✅ Integration test complete!"