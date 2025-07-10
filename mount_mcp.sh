#!/bin/bash

[ -f "./node_modules/.bin/claude" ] || npm install @anthropic-ai/claude-code

cat cloudflare-mcp.txt | grep -v ^\$ | while read a; do
  ./node_modules/.bin/claude mcp add --transport sse cloudflare-${a} "https://${a}.mcp.cloudflare.com/sse"
done
