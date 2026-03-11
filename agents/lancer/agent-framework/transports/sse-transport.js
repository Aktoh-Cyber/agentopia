/**
 * SSE Transport Class - Provides Server-Sent Events streaming for MCP agents
 *
 * This transport enables real-time streaming of AI responses to clients,
 * compatible with the MCP protocol's SSE transport specification.
 */

export class SSETransport {
  constructor() {
    this.encoder = new TextEncoder();
    this.stream = null;
    this.controller = null;
    this.closed = false;
  }

  /**
   * Initialize the SSE stream
   * @returns {ReadableStream} The readable stream for the response
   */
  initialize() {
    const self = this;
    this.stream = new ReadableStream({
      start(controller) {
        self.controller = controller;
      },
      cancel() {
        self.closed = true;
      }
    });
    return this.stream;
  }

  /**
   * Get SSE-specific headers
   * @returns {Object} Headers for SSE response
   */
  getHeaders() {
    return {
      'Content-Type': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive',
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };
  }

  /**
   * Get the Response object for SSE
   * @returns {Response} HTTP Response with SSE stream
   */
  getResponse() {
    if (!this.stream) {
      this.initialize();
    }
    return new Response(this.stream, {
      headers: this.getHeaders(),
    });
  }

  /**
   * Send a named SSE event
   * @param {string} eventType - The event type (e.g., 'chunk', 'complete', 'error')
   * @param {any} data - The data to send (will be JSON stringified if object)
   */
  sendEvent(eventType, data) {
    if (this.closed || !this.controller) {
      return;
    }

    const dataStr = typeof data === 'object' ? JSON.stringify(data) : String(data);
    const message = `event: ${eventType}\ndata: ${dataStr}\n\n`;

    try {
      this.controller.enqueue(this.encoder.encode(message));
    } catch (error) {
      console.error('SSE sendEvent error:', error);
    }
  }

  /**
   * Send a text chunk (for streaming responses)
   * @param {string} chunk - The text chunk to send
   */
  sendChunk(chunk) {
    this.sendEvent('chunk', { text: chunk });
  }

  /**
   * Send metadata about the response
   * @param {Object} metadata - Metadata object
   */
  sendMetadata(metadata) {
    this.sendEvent('metadata', metadata);
  }

  /**
   * Send a start event to indicate streaming has begun
   * @param {Object} info - Optional info about the stream
   */
  sendStart(info = {}) {
    this.sendEvent('start', { timestamp: Date.now(), ...info });
  }

  /**
   * Send a cached response (full message)
   * @param {string} response - The cached response text
   */
  sendCached(response) {
    this.sendEvent('message', { text: response, cached: true });
  }

  /**
   * Send the complete event and close the stream
   * @param {Object} response - The final response data
   */
  sendComplete(response) {
    this.sendEvent('complete', {
      timestamp: Date.now(),
      ...response
    });
    this.close();
  }

  /**
   * Send an error event
   * @param {string} message - Error message
   * @param {number} code - Error code (optional)
   */
  sendError(message, code = -32603) {
    this.sendEvent('error', { message, code });
    this.close();
  }

  /**
   * Close the SSE stream
   */
  close() {
    if (!this.closed && this.controller) {
      try {
        this.controller.close();
      } catch (error) {
        // Stream may already be closed
      }
      this.closed = true;
    }
  }
}

/**
 * MCP SSE Transport - Handles MCP protocol over SSE
 *
 * This provides a compatible interface for MCP clients expecting SSE transport.
 */
export class MCPSSETransport extends SSETransport {
  constructor(sessionId = null) {
    super();
    this.sessionId = sessionId || crypto.randomUUID();
    this.messageId = 0;
  }

  /**
   * Send an MCP JSON-RPC response
   * @param {number} id - Request ID
   * @param {any} result - Result data
   */
  sendResult(id, result) {
    this.sendEvent('message', {
      jsonrpc: '2.0',
      id,
      result
    });
  }

  /**
   * Send an MCP JSON-RPC error
   * @param {number} id - Request ID
   * @param {number} code - Error code
   * @param {string} message - Error message
   */
  sendMCPError(id, code, message) {
    this.sendEvent('message', {
      jsonrpc: '2.0',
      id,
      error: { code, message }
    });
  }

  /**
   * Send an MCP notification
   * @param {string} method - Notification method
   * @param {Object} params - Notification params
   */
  sendNotification(method, params = {}) {
    this.sendEvent('message', {
      jsonrpc: '2.0',
      method,
      params
    });
  }

  /**
   * Send session info on connection
   */
  sendSessionInfo() {
    this.sendEvent('endpoint', `/mcp/session/${this.sessionId}`);
  }
}

export default SSETransport;
