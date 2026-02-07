# Agentopia SSE Transport - Quick Reference Guide

## Current Architecture (HTTP POST Only)

```
Client
  ↓
  POST /api/ask
  ├── request: { question: "..." }
  ├── full wait for response
  └── response: { answer: "...", cached: bool }
  ↓
Server (BaseAgent.fetch)
  ├── processQuestion() → LangChain chain
  ├── Cache check → KV lookup
  ├── LLM call → Cloudflare AI
  └── Cache write → KV store
```

---

## Proposed SSE Architecture (Streaming)

```
Client
  ├─→ Try: GET /api/ask/stream?question=...
  │   ├─ EventSource listener
  │   ├─ Receive events:
  │   │  ├─ event: chunk → Partial response text
  │   │  ├─ event: metadata → Response info
  │   │  └─ event: complete → Final response
  │   └─ Progressive rendering (real-time display)
  │
  └─→ Fallback: POST /api/ask (if no SSE support)
      └─ Existing HTTP behavior (unchanged)

Server (BaseAgent.fetch)
  ├─ GET /api/ask/stream
  │  ├─ Create SSETransport
  │  ├─ processQuestionStream()
  │  │  ├─ Cache check
  │  │  ├─ Stream LLM output via transport
  │  │  ├─ Send chunks via SSE events
  │  │  └─ Cache completed response
  │  └─ Return ReadableStream
  │
  ├─ POST /api/ask (UNCHANGED)
  │  └─ Existing behavior preserved
  │
  └─ POST /mcp (UNCHANGED)
     └─ MCP protocol endpoint
```

---

## Core Components to Implement

### 1. SSETransport Class

**File**: `/agents/agent-framework/transports/sse-transport.js`

```javascript
class SSETransport {
  async sendChunk(chunk)      // Send partial response
  async sendEvent(type, data) // Send named event
  async sendComplete(response)// Send final event & close
  async sendError(error)      // Send error event
  getHeaders()               // Return SSE headers
  getResponse()              // Return Response object
}
```

**Methods Called By**:
- `processQuestionStream()` in BaseAgent
- RouterAgent for specialized streaming

**Event Types Emitted**:
```
start       → Stream beginning
chunk       → Response chunk
metadata    → Response metadata
message     → Cached response
complete    → Stream end
error       → Stream error
```

### 2. BaseAgent.processQuestionStream()

**File**: `/agents/agent-framework/base-agent.js`

```javascript
async processQuestionStream(env, question, transport) {
  // Similar to processQuestion() but:
  // 1. Streams output via transport
  // 2. Sends events for each chunk
  // 3. Caches completed response
  // 4. Handles LangChain streaming
}
```

**Called From**:
- New `GET /api/ask/stream` endpoint handler
- RouterAgent (for streaming routing)

**Cache Behavior**:
- Check cache BEFORE streaming
- If cached → Send via `message` event (fast path)
- If not cached → Stream from LLM

### 3. Fetch Handler Addition

**File**: `/agents/agent-framework/base-agent.js` (fetch method)

```javascript
// Add NEW handler AFTER POST /api/ask
if (request.method === 'GET' && url.pathname === '/api/ask/stream') {
  // Create SSETransport
  // Call processQuestionStream()
  // Return SSE response
}
```

**Preserved Handlers**:
- `GET /` → Homepage (unchanged)
- `POST /api/ask` → HTTP POST (unchanged)
- `POST /mcp` → MCP protocol (unchanged)
- `OPTIONS` → CORS (unchanged)

### 4. Client-Side Detection & Fallback

**File**: Inside `getClientScript()` method

```javascript
// Detect SSE support
if (typeof EventSource !== 'undefined') {
  // Use SSE endpoint
  askQuestionSSE(question, loadingId)
} else {
  // Fallback to HTTP POST
  askQuestionHTTP(question, loadingId)
}
```

**EventSource Listeners**:
```javascript
es.addEventListener('chunk', e => {/*...*/})
es.addEventListener('message', e => {/*...*/})
es.addEventListener('complete', e => {/*...*/})
es.addEventListener('error', e => {/*...*/})
```

---

## File Structure After Implementation

```
agents/agent-framework/
├── base-agent.js (MODIFIED)
│   ├── Add: processQuestionStream()
│   ├── Add: GET /api/ask/stream handler
│   └── Update: getClientScript()
│
├── transports/ (NEW DIRECTORY)
│   ├── transport.js (interface definition)
│   ├── http-post-transport.js (wrapper for HTTP POST)
│   └── sse-transport.js (NEW SSE implementation)
│
└── [other existing files unchanged]
```

---

## Implementation Checklist

### Phase 1: Core SSE (Priority: HIGH)
- [ ] Create `transports/sse-transport.js`
- [ ] Add `processQuestionStream()` to BaseAgent
- [ ] Add `GET /api/ask/stream` handler
- [ ] Update client script for SSE
- [ ] Test locally with wrangler dev
- [ ] Deploy to staging
- [ ] Verify both HTTP and SSE work

### Phase 2: LangChain Integration (Priority: HIGH)
- [ ] Integrate `chain.stream()` or equivalent
- [ ] Handle streaming from LLM
- [ ] Format chunks properly
- [ ] Test with different response sizes
- [ ] Add timeout handling

### Phase 3: Caching & Optimization (Priority: MEDIUM)
- [ ] Cache fast path for SSE
- [ ] Cache completed streamed responses
- [ ] Add metadata events
- [ ] Measure performance impact
- [ ] Optimize chunk size

### Phase 4: Router Agent (Priority: MEDIUM)
- [ ] Update RouterAgent for streaming
- [ ] Stream specialized agent responses
- [ ] Handle routing metadata
- [ ] Test multi-agent streaming

### Phase 5: Client Enhancement (Priority: MEDIUM)
- [ ] Progressive rendering
- [ ] Network status indicators
- [ ] Retry/reconnection logic
- [ ] UX improvements

### Phase 6: Python Port (Priority: LOW)
- [ ] Port SSE transport to Python
- [ ] Handle async in Pyodide
- [ ] Test with Python agents

---

## Testing Strategy

### Unit Tests
```
SSETransport
├─ sendChunk() formats correctly
├─ sendEvent() includes event type
├─ sendComplete() sends final event
└─ getHeaders() returns SSE headers

BaseAgent.processQuestionStream()
├─ Cache hit returns cached response
├─ Cache miss streams response
├─ Error events sent on failure
└─ Completion event sent correctly
```

### Integration Tests
```
HTTP POST
├─ POST /api/ask still works
├─ Response format unchanged
└─ Caching still works

SSE Streaming
├─ GET /api/ask/stream works
├─ EventSource connects
├─ Chunk events received
├─ Complete event received
└─ Error handling works

Fallback
├─ Browser without SSE uses HTTP
├─ Both return same answer
└─ Cache is shared
```

### Load Tests
```
├─ Multiple concurrent streams
├─ Long responses (10k+ chars)
├─ Rapid requests
├─ Memory usage
└─ CPU usage
```

---

## Performance Expectations

### HTTP POST (Current)
- **Latency to First Byte**: Full response time (2-5s)
- **User Perception**: Spinner while waiting
- **Bandwidth**: Single request/response
- **Cache Hit**: Instant response

### SSE Streaming (New)
- **Latency to First Byte**: ~100-200ms (first token)
- **User Perception**: Progressive text appearance
- **Bandwidth**: Same total (streaming instead of bulk)
- **Cache Hit**: Instant response (same as HTTP)

---

## Key Design Decisions

### Why SSE?
- One-way server→client (perfect for AI responses)
- Built-in reconnection
- Native browser support
- Works with Cloudflare Workers
- Simpler than WebSockets

### Why GET /api/ask/stream?
- EventSource requires GET
- Query params for simple initiation
- Standard SSE pattern
- Compatible with browser security

### Why Keep HTTP POST?
- Backward compatibility
- Simple for API clients
- Works in all environments
- No client-side changes needed

### Why Separate Transport Layer?
- Single responsibility (request transport)
- Easy to add future transports (gRPC, WebSocket)
- Shared processing pipeline
- Cleaner architecture

---

## Migration Guide

### For Existing Clients
**No changes required!** The `/api/ask` HTTP POST endpoint remains unchanged.

### For New Clients
```javascript
// Option 1: Try SSE, fallback to HTTP (recommended)
const supportsSSE = typeof EventSource !== 'undefined';
if (supportsSSE) {
  useSSE();  // Progressive streaming
} else {
  useHTTP(); // Works on all browsers
}

// Option 2: Always use HTTP (simple)
fetch('/api/ask', {
  method: 'POST',
  body: JSON.stringify({ question })
})

// Option 3: Always use SSE (modern browsers only)
const es = new EventSource(`/api/ask/stream?question=...`);
```

---

## Troubleshooting

### "No chunks received"
- [ ] Check EventSource connection status
- [ ] Verify /api/ask/stream endpoint returns 200 OK
- [ ] Check browser console for errors
- [ ] Try fallback to HTTP POST

### "Connection closes early"
- [ ] Check for Cloudflare Worker timeout (50s limit)
- [ ] Ensure processQuestionStream() handles timeouts
- [ ] Add error events to transport
- [ ] Check for network interruptions

### "Chunks arrive out of order"
- [ ] Normal with streaming - combine in order
- [ ] Client should concatenate all chunks
- [ ] Final `complete` event has full answer

### "High latency"
- [ ] Check LLM response time (Cloudflare AI)
- [ ] Monitor chunk size (too small = overhead)
- [ ] Check network latency to user
- [ ] Consider HTTP POST for very fast networks

---

## References

**Documentation Files**:
- `SSE_TRANSPORT_ARCHITECTURE.md` - Full design document
- `CLAUDE.md` - Framework overview
- `COMPREHENSIVE_ANALYSIS.md` - Detailed analysis

**External Resources**:
- [MDN: Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [LangChain.js Streaming](https://js.langchain.com/docs/guides/streaming)
- [Cloudflare Workers](https://developers.cloudflare.com/workers/)

**Code Files**:
- `/agents/agent-framework/base-agent.js` - Core implementation
- `/agents/judge-js/src/index.js` - Example agent
- `/agents/infosec/src/index.js` - Router agent example

