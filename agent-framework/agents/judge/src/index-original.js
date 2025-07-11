export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    
    // Handle CORS
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    // Handle preflight requests
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Serve homepage
    if (request.method === 'GET' && url.pathname === '/') {
      return new Response(getHomePage(), {
        headers: {
          'Content-Type': 'text/html',
          ...corsHeaders,
        },
      });
    }

    // Handle MCP requests (Model Context Protocol)
    if (request.method === 'POST' && url.pathname === '/mcp') {
      try {
        const mcpRequest = await request.json();
        
        if (mcpRequest.method === 'tools/list') {
          return new Response(JSON.stringify({
            tools: [{
              name: 'judge_vulnerability_compliance',
              description: 'Ask Judge about vulnerabilities, CVEs, compliance frameworks, and security requirements',
              inputSchema: {
                type: 'object',
                properties: {
                  question: {
                    type: 'string',
                    description: 'Question about vulnerabilities or compliance'
                  }
                },
                required: ['question']
              }
            }]
          }), {
            headers: {
              'Content-Type': 'application/json',
              ...corsHeaders,
            },
          });
        }
        
        if (mcpRequest.method === 'tools/call' && mcpRequest.params?.name === 'judge_vulnerability_compliance') {
          const question = mcpRequest.params?.arguments?.question;
          
          if (!question) {
            return new Response(JSON.stringify({
              error: {
                code: -32602,
                message: 'Invalid params: question is required'
              }
            }), {
              status: 400,
              headers: {
                'Content-Type': 'application/json',
                ...corsHeaders,
              },
            });
          }
          
          // Process the question through Judge
          const systemPrompt = `You are a specialized cybersecurity expert focused on vulnerability assessment and compliance. Your expertise includes:
        - CVE database and vulnerability scoring (CVSS)
        - Security frameworks (NIST, ISO 27001, SOC 2, GDPR, HIPAA, PCI-DSS)
        - Vulnerability scanning and assessment methodologies
        - Compliance auditing and gap analysis
        - Risk assessment and remediation strategies
        - Security controls and compensating measures
        
        Provide detailed, authoritative answers about vulnerabilities, compliance requirements, and risk management.
        Include specific CVE references, compliance clause numbers, and actionable remediation steps when relevant.
        If a question is not related to vulnerabilities or compliance, politely redirect to these topics.`;
          
          const response = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
            messages: [
              { role: 'system', content: systemPrompt },
              { role: 'user', content: `Question: ${question}` }
            ],
            max_tokens: parseInt(env.MAX_TOKENS || '512'),
            temperature: parseFloat(env.TEMPERATURE || '0.3'),
          });
          
          return new Response(JSON.stringify({
            content: [{
              type: 'text',
              text: response.response || 'I apologize, but I could not generate a response. Please try again.'
            }]
          }), {
            headers: {
              'Content-Type': 'application/json',
              ...corsHeaders,
            },
          });
        }
        
        return new Response(JSON.stringify({
          error: {
            code: -32601,
            message: 'Method not found'
          }
        }), {
          status: 404,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders,
          },
        });
        
      } catch (error) {
        console.error('Error processing MCP request:', error);
        return new Response(JSON.stringify({
          error: {
            code: -32603,
            message: 'Internal error'
          }
        }), {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders,
          },
        });
      }
    }
    
    // Handle API requests
    if (request.method === 'POST' && url.pathname === '/api/ask') {
      try {
        const { question } = await request.json();
        
        if (!question || question.trim().length === 0) {
          return new Response(JSON.stringify({ error: 'Question is required' }), {
            status: 400,
            headers: {
              'Content-Type': 'application/json',
              ...corsHeaders,
            },
          });
        }

        // Check cache first
        const cacheKey = `q:${question.toLowerCase().trim()}`;
        const cached = await env.CACHE?.get(cacheKey);
        if (cached) {
          return new Response(JSON.stringify({ answer: cached, cached: true }), {
            headers: {
              'Content-Type': 'application/json',
              ...corsHeaders,
            },
          });
        }

        // Prepare the prompt with vulnerability and compliance context
        const systemPrompt = `You are a specialized cybersecurity expert focused on vulnerability assessment and compliance. Your expertise includes:
        - CVE database and vulnerability scoring (CVSS)
        - Security frameworks (NIST, ISO 27001, SOC 2, GDPR, HIPAA, PCI-DSS)
        - Vulnerability scanning and assessment methodologies
        - Compliance auditing and gap analysis
        - Risk assessment and remediation strategies
        - Security controls and compensating measures
        
        Provide detailed, authoritative answers about vulnerabilities, compliance requirements, and risk management.
        Include specific CVE references, compliance clause numbers, and actionable remediation steps when relevant.
        If a question is not related to vulnerabilities or compliance, politely redirect to these topics.`;

        const userPrompt = `Question: ${question}`;

        // Call the AI model - using Llama 3.1 8B Instruct for speed and cost efficiency
        const response = await env.AI.run('@cf/meta/llama-3.1-8b-instruct', {
          messages: [
            { role: 'system', content: systemPrompt },
            { role: 'user', content: userPrompt }
          ],
          max_tokens: parseInt(env.MAX_TOKENS || '512'),
          temperature: parseFloat(env.TEMPERATURE || '0.3'),
        });

        const answer = response.response || 'I apologize, but I could not generate a response. Please try again.';

        // Cache the response for 1 hour
        if (env.CACHE) {
          await env.CACHE.put(cacheKey, answer, { expirationTtl: 3600 });
        }

        return new Response(JSON.stringify({ answer, cached: false }), {
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders,
          },
        });

      } catch (error) {
        console.error('Error processing request:', error);
        return new Response(JSON.stringify({ error: 'An error occurred processing your request' }), {
          status: 500,
          headers: {
            'Content-Type': 'application/json',
            ...corsHeaders,
          },
        });
      }
    }

    // Return 404 for unhandled routes
    return new Response('Not Found', { status: 404 });
  },
};

function getHomePage() {
  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Judge - Vulnerability & Compliance Expert - MindHive.tech</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #0a0e27;
            color: #e0e6ed;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }
        
        header {
            background: #1a1f3a;
            padding: 1.5rem;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
        }
        
        h1 {
            text-align: center;
            color: #00d4ff;
            font-size: 2rem;
        }
        
        .subtitle {
            text-align: center;
            color: #8892b0;
            margin-top: 0.5rem;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
            padding: 2rem;
            flex: 1;
        }
        
        .chat-box {
            background: #1a1f3a;
            border-radius: 10px;
            padding: 2rem;
            margin-top: 2rem;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }
        
        .input-group {
            display: flex;
            gap: 1rem;
            margin-bottom: 2rem;
        }
        
        input {
            flex: 1;
            padding: 1rem;
            border: 2px solid #2a3f5f;
            background: #0a0e27;
            color: #e0e6ed;
            border-radius: 5px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        
        input:focus {
            outline: none;
            border-color: #00d4ff;
        }
        
        button {
            padding: 1rem 2rem;
            background: #00d4ff;
            color: #0a0e27;
            border: none;
            border-radius: 5px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: background 0.3s;
        }
        
        button:hover {
            background: #00a8cc;
        }
        
        button:disabled {
            background: #2a3f5f;
            cursor: not-allowed;
        }
        
        .messages {
            max-height: 400px;
            overflow-y: auto;
            padding-right: 1rem;
        }
        
        .message {
            margin-bottom: 1.5rem;
            padding: 1rem;
            border-radius: 8px;
            animation: fadeIn 0.3s ease-in;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .user-message {
            background: #2a3f5f;
            border-left: 3px solid #00d4ff;
        }
        
        .ai-message {
            background: #0f1729;
            border-left: 3px solid #64ffda;
        }
        
        .message-label {
            font-weight: bold;
            margin-bottom: 0.5rem;
            color: #64ffda;
        }
        
        .user-message .message-label {
            color: #00d4ff;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #2a3f5f;
            border-radius: 50%;
            border-top-color: #00d4ff;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .error {
            color: #ff6b6b;
            padding: 1rem;
            background: rgba(255, 107, 107, 0.1);
            border-radius: 5px;
            margin-top: 1rem;
        }
        
        .examples {
            margin-top: 2rem;
            padding: 1rem;
            background: rgba(100, 255, 218, 0.05);
            border-radius: 8px;
        }
        
        .examples h3 {
            color: #64ffda;
            margin-bottom: 1rem;
        }
        
        .examples ul {
            list-style: none;
            padding-left: 0;
        }
        
        .examples li {
            margin-bottom: 0.5rem;
            padding-left: 1.5rem;
            position: relative;
        }
        
        .examples li:before {
            content: "▸";
            position: absolute;
            left: 0;
            color: #64ffda;
        }
        
        footer {
            text-align: center;
            padding: 2rem;
            color: #8892b0;
            background: #1a1f3a;
        }
        
        a {
            color: #00d4ff;
            text-decoration: none;
        }
        
        a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <header>
        <h1>⚖️ Judge - Vulnerability & Compliance Expert</h1>
        <p class="subtitle">Specialized AI for Security Vulnerabilities and Compliance | MindHive.tech</p>
    </header>
    
    <div class="container">
        <div class="chat-box">
            <div class="input-group">
                <input 
                    type="text" 
                    id="questionInput" 
                    placeholder="Ask about vulnerabilities or compliance..."
                    autofocus
                />
                <button id="askButton" onclick="askQuestion()">Ask</button>
            </div>
            
            <div id="messages" class="messages"></div>
            
            <div class="examples">
                <h3>Example Questions:</h3>
                <ul>
                    <li>What is CVE-2021-44228 (Log4Shell) and how do I remediate it?</li>
                    <li>What are the key requirements for SOC 2 Type II compliance?</li>
                    <li>How do I calculate CVSS scores for vulnerabilities?</li>
                    <li>What are the GDPR requirements for data breach notification?</li>
                    <li>What controls are needed for PCI-DSS compliance at Level 1?</li>
                </ul>
            </div>
        </div>
    </div>
    
    <footer>
        <p>Built with Cloudflare Workers AI | <a href="https://mindhive.tech">MindHive.tech</a></p>
    </footer>
    
    <script>
        const messagesDiv = document.getElementById('messages');
        const questionInput = document.getElementById('questionInput');
        const askButton = document.getElementById('askButton');
        
        questionInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                askQuestion();
            }
        });
        
        async function askQuestion() {
            const question = questionInput.value.trim();
            if (!question) return;
            
            // Disable input
            questionInput.disabled = true;
            askButton.disabled = true;
            
            // Add user message
            addMessage(question, 'user');
            
            // Clear input
            questionInput.value = '';
            
            // Add loading message
            const loadingId = 'loading-' + Date.now();
            addMessage('<div class="loading"></div> Thinking...', 'ai', loadingId);
            
            try {
                const response = await fetch('/api/ask', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({ question }),
                });
                
                const data = await response.json();
                
                // Remove loading message
                document.getElementById(loadingId)?.remove();
                
                if (response.ok) {
                    addMessage(data.answer, 'ai');
                } else {
                    addMessage('Error: ' + (data.error || 'Something went wrong'), 'ai');
                }
            } catch (error) {
                // Remove loading message
                document.getElementById(loadingId)?.remove();
                addMessage('Error: Could not connect to the server', 'ai');
            }
            
            // Re-enable input
            questionInput.disabled = false;
            askButton.disabled = false;
            questionInput.focus();
        }
        
        function addMessage(content, type, id) {
            const messageDiv = document.createElement('div');
            messageDiv.className = 'message ' + type + '-message';
            if (id) messageDiv.id = id;
            
            const label = document.createElement('div');
            label.className = 'message-label';
            label.textContent = type === 'user' ? 'You:' : 'Judge:';
            
            const contentDiv = document.createElement('div');
            contentDiv.innerHTML = content;
            
            messageDiv.appendChild(label);
            messageDiv.appendChild(contentDiv);
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }
    </script>
</body>
</html>`;
}