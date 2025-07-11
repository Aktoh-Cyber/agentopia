"""
Agent Generator Agent - Main implementation
"""

from typing import Any

from .base_agent import BaseAgent
from .enhanced_agent_generator import EnhancedAgentGenerator


class GeneratorAgent(BaseAgent):
    """Specialized agent for generating other agents"""

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self.generator = None  # Initialized when GitHub token is available

    def _init_generator(self, env) -> EnhancedAgentGenerator:
        """Initialize the generator with GitHub credentials"""
        if self.generator is None:
            github_token = getattr(env, "GITHUB_TOKEN", None)
            repo_owner = getattr(env, "GITHUB_REPO_OWNER", "your-org")
            repo_name = getattr(env, "GITHUB_REPO_NAME", "agent-framework")

            if not github_token:
                raise ValueError("GITHUB_TOKEN environment variable is required")

            self.generator = EnhancedAgentGenerator(github_token, repo_owner, repo_name)

        return self.generator

    async def handle_generation_request(self, request_data: dict[str, Any], env) -> dict[str, Any]:
        """Handle agent generation request"""
        try:
            generator = self._init_generator(env)

            # Extract configuration from request
            agent_config = request_data.get("config", {})
            language = request_data.get("language", "python")

            # Validate minimum required fields
            required_fields = ["name", "description", "type"]
            missing_fields = [field for field in required_fields if not agent_config.get(field)]

            if missing_fields:
                return {
                    "success": False,
                    "error": f"Missing required fields: {', '.join(missing_fields)}",
                    "required_fields": {
                        "name": "Agent name (e.g., 'Threat Intel Expert')",
                        "description": "Brief description of the agent's purpose",
                        "type": "Either 'router' or 'specialist'",
                        "domain": "Cloudflare domain for the agent",
                        "systemPrompt": "AI system prompt defining behavior",
                        "accountId": "Cloudflare account ID",
                        "zoneId": "Cloudflare zone ID",
                    },
                }

            # Generate and commit the agent
            result = await generator.generate_and_commit_agent(agent_config, language)

            return result

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "suggestion": "Please check your configuration and GitHub credentials",
            }

    async def handle_mcp_call(self, method: str, params: dict[str, Any], env) -> dict[str, Any]:
        """Handle MCP tool calls"""
        if method == "generate_agent":
            return await self.handle_generation_request(params, env)
        elif method == "list_templates":
            return {
                "success": True,
                "templates": {
                    "specialist": {
                        "description": "Specialist agent for specific domain expertise",
                        "required_fields": [
                            "name",
                            "description",
                            "expertise",
                            "keywords",
                            "domain",
                            "systemPrompt",
                            "accountId",
                            "zoneId",
                        ],
                        "optional_fields": ["patterns", "priority", "examples", "mcpToolName"],
                    },
                    "router": {
                        "description": "Router agent that coordinates multiple specialists",
                        "required_fields": [
                            "name",
                            "description",
                            "domain",
                            "systemPrompt",
                            "accountId",
                            "zoneId",
                            "registry",
                        ],
                        "optional_fields": ["examples"],
                    },
                },
            }
        elif method == "validate_config":
            try:
                generator = self._init_generator(env)
                config = params.get("config", {})
                language = params.get("language", "python")

                # Validate by preparing config (will raise if invalid)
                prepared_config = generator.prepare_config(config, language)

                return {
                    "success": True,
                    "valid": True,
                    "prepared_config": prepared_config,
                    "worker_name": generator.make_worker_name(config["name"]),
                }
            except Exception as e:
                return {"success": True, "valid": False, "error": str(e)}
        else:
            return {
                "success": False,
                "error": f"Unknown method: {method}",
                "available_methods": ["generate_agent", "list_templates", "validate_config"],
            }

    def generate_web_ui(self, env) -> str:
        """Generate enhanced web UI for agent generation"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{self.config['name']}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #ff6b6b, #ffa726);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 15px;
        }}

        .header p {{
            font-size: 1.2em;
            opacity: 0.9;
        }}

        .content {{
            padding: 40px;
        }}

        .tabs {{
            display: flex;
            margin-bottom: 30px;
            border-bottom: 2px solid #f0f0f0;
        }}

        .tab {{
            padding: 15px 25px;
            background: none;
            border: none;
            font-size: 16px;
            cursor: pointer;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.3s ease;
        }}

        .tab.active {{
            color: #667eea;
            border-bottom-color: #667eea;
            font-weight: bold;
        }}

        .tab-content {{
            display: none;
        }}

        .tab-content.active {{
            display: block;
        }}

        .form-group {{
            margin-bottom: 25px;
        }}

        .form-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 25px;
        }}

        label {{
            display: block;
            margin-bottom: 8px;
            font-weight: bold;
            color: #333;
        }}

        input, textarea, select {{
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s ease;
        }}

        input:focus, textarea:focus, select:focus {{
            outline: none;
            border-color: #667eea;
        }}

        textarea {{
            resize: vertical;
            min-height: 120px;
        }}

        .button {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: transform 0.2s ease;
            margin-right: 10px;
        }}

        .button:hover {{
            transform: translateY(-2px);
        }}

        .button:disabled {{
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }}

        .result {{
            margin-top: 30px;
            padding: 20px;
            border-radius: 8px;
            display: none;
        }}

        .result.success {{
            background: #d4edda;
            border: 1px solid #c3e6cb;
            color: #155724;
        }}

        .result.error {{
            background: #f8d7da;
            border: 1px solid #f5c6cb;
            color: #721c24;
        }}

        .result.loading {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            color: #856404;
        }}

        .info-section {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
        }}

        .info-section h3 {{
            color: #495057;
            margin-bottom: 15px;
        }}

        .info-section ul {{
            list-style: none;
            padding-left: 0;
        }}

        .info-section li {{
            padding: 8px 0;
            border-bottom: 1px solid #dee2e6;
        }}

        .info-section li:last-child {{
            border-bottom: none;
        }}

        .examples {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 20px;
        }}

        .example-card {{
            background: white;
            border: 2px solid #e9ecef;
            border-radius: 8px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}

        .example-card:hover {{
            border-color: #667eea;
            transform: translateY(-2px);
        }}

        .example-card h4 {{
            color: #495057;
            margin-bottom: 10px;
        }}

        .example-card p {{
            color: #6c757d;
            font-size: 14px;
        }}

        .tag {{
            display: inline-block;
            background: #e9ecef;
            color: #495057;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            margin-right: 5px;
            margin-top: 5px;
        }}

        @media (max-width: 768px) {{
            .form-row {{
                grid-template-columns: 1fr;
            }}

            .header h1 {{
                font-size: 2em;
            }}

            .content {{
                padding: 20px;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>
                <span>{self.config.get('icon', '🏭')}</span>
                {self.config['name']}
            </h1>
            <p>{self.config['description']}</p>
        </div>

        <div class="content">
            <div class="tabs">
                <button class="tab active" onclick="switchTab('generator')">🚀 Generate Agent</button>
                <button class="tab" onclick="switchTab('examples')">📚 Examples</button>
                <button class="tab" onclick="switchTab('docs')">📖 Documentation</button>
            </div>

            <!-- Generator Tab -->
            <div class="tab-content active" id="generator">
                <form id="agentForm">
                    <div class="form-row">
                        <div class="form-group">
                            <label for="agentType">Agent Type *</label>
                            <select id="agentType" name="type" required>
                                <option value="">Select agent type...</option>
                                <option value="specialist">Specialist Agent</option>
                                <option value="router">Router Agent</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label for="language">Language *</label>
                            <select id="language" name="language" required>
                                <option value="python">Python</option>
                                <option value="javascript">JavaScript</option>
                            </select>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label for="name">Agent Name *</label>
                            <input type="text" id="name" name="name" placeholder="e.g., Threat Intelligence Expert" required>
                        </div>
                        <div class="form-group">
                            <label for="domain">Domain *</label>
                            <input type="text" id="domain" name="domain" placeholder="e.g., threat-intel.yourdomain.com" required>
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="description">Description *</label>
                        <textarea id="description" name="description" placeholder="Brief description of what this agent does..." required></textarea>
                    </div>

                    <div class="form-group">
                        <label for="systemPrompt">System Prompt *</label>
                        <textarea id="systemPrompt" name="systemPrompt" placeholder="Define how the AI should behave and respond..." required style="min-height: 150px;"></textarea>
                    </div>

                    <div id="specialistFields" style="display: none;">
                        <div class="form-group">
                            <label for="expertise">Expertise</label>
                            <input type="text" id="expertise" name="expertise" placeholder="e.g., threat intelligence and IOC analysis">
                        </div>

                        <div class="form-group">
                            <label for="keywords">Keywords (comma-separated)</label>
                            <textarea id="keywords" name="keywords" placeholder="threat, intel, ioc, indicator, malware..." style="min-height: 80px;"></textarea>
                        </div>

                        <div class="form-group">
                            <label for="patterns">Regex Patterns (comma-separated, optional)</label>
                            <textarea id="patterns" name="patterns" placeholder="CVE-\\\\d{{4}}-\\\\d+, \\\\b(IOC|indicator)\\\\b" style="min-height: 80px;"></textarea>
                        </div>
                    </div>

                    <div class="form-row">
                        <div class="form-group">
                            <label for="accountId">Cloudflare Account ID *</label>
                            <input type="text" id="accountId" name="accountId" placeholder="Your Cloudflare account ID" required>
                        </div>
                        <div class="form-group">
                            <label for="zoneId">Cloudflare Zone ID *</label>
                            <input type="text" id="zoneId" name="zoneId" placeholder="Your Cloudflare zone ID" required>
                        </div>
                    </div>

                    <div class="form-group">
                        <label for="examples">Example Questions (one per line, optional)</label>
                        <textarea id="examples" name="examples" placeholder="What are the latest threat indicators?\\nAnalyze this IOC for me\\nShow me recent malware families" style="min-height: 100px;"></textarea>
                    </div>

                    <button type="submit" class="button">🚀 Generate Agent</button>
                    <button type="button" class="button" onclick="validateConfig()">✅ Validate Config</button>
                </form>

                <div id="result" class="result"></div>
            </div>

            <!-- Examples Tab -->
            <div class="tab-content" id="examples">
                <div class="info-section">
                    <h3>Quick Start Examples</h3>
                    <p>Click on any example to populate the form with pre-configured settings:</p>
                </div>

                <div class="examples">
                    <div class="example-card" onclick="loadExample('threatIntel')">
                        <h4>🔍 Threat Intelligence Specialist</h4>
                        <p>Specialized agent for analyzing threats, IOCs, and security indicators</p>
                        <span class="tag">Python</span>
                        <span class="tag">Specialist</span>
                    </div>

                    <div class="example-card" onclick="loadExample('securityRouter')">
                        <h4>🛡️ Security Router</h4>
                        <p>Router agent that coordinates multiple security specialists</p>
                        <span class="tag">Python</span>
                        <span class="tag">Router</span>
                    </div>

                    <div class="example-card" onclick="loadExample('codeAnalyst')">
                        <h4>📊 Code Security Analyst</h4>
                        <p>Specialist for code vulnerability analysis and security reviews</p>
                        <span class="tag">JavaScript</span>
                        <span class="tag">Specialist</span>
                    </div>

                    <div class="example-card" onclick="loadExample('financeExpert')">
                        <h4>💰 Financial Analysis Expert</h4>
                        <p>Specialized agent for financial data analysis and insights</p>
                        <span class="tag">Python</span>
                        <span class="tag">Specialist</span>
                    </div>
                </div>
            </div>

            <!-- Documentation Tab -->
            <div class="tab-content" id="docs">
                <div class="info-section">
                    <h3>🚀 Agent Generation Process</h3>
                    <ul>
                        <li><strong>Configuration:</strong> Fill out the form with your agent requirements</li>
                        <li><strong>Generation:</strong> System creates all necessary files (Python/JS code, config, docs)</li>
                        <li><strong>GitHub Commit:</strong> Files are committed to a new branch automatically</li>
                        <li><strong>Pull Request:</strong> A PR is created for review and validation</li>
                        <li><strong>CI/CD Pipeline:</strong> GitHub Actions validate and deploy the agent</li>
                        <li><strong>Live Agent:</strong> Your agent is deployed to Cloudflare Workers</li>
                    </ul>
                </div>

                <div class="info-section">
                    <h3>📊 Agent Types</h3>
                    <ul>
                        <li><strong>Specialist Agents:</strong> Focus on specific domains with expert knowledge</li>
                        <li><strong>Router Agents:</strong> Coordinate multiple specialists and route questions intelligently</li>
                    </ul>
                </div>

                <div class="info-section">
                    <h3>🛠️ Technical Details</h3>
                    <ul>
                        <li><strong>Languages:</strong> Python (standard library + FFI) or JavaScript (full ecosystem)</li>
                        <li><strong>Deployment:</strong> Cloudflare Workers with edge computing</li>
                        <li><strong>MCP Protocol:</strong> All agents support Model Context Protocol</li>
                        <li><strong>Caching:</strong> Built-in response caching for performance</li>
                        <li><strong>Monitoring:</strong> Automatic logging and observability</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <script>
        const examples = {{
            threatIntel: {{
                type: 'specialist',
                language: 'python',
                name: 'Threat Intelligence Expert',
                domain: 'threat-intel.yourdomain.com',
                description: 'Specialized AI for threat intelligence analysis, IOC investigation, and security research',
                systemPrompt: 'You are a threat intelligence expert specializing in:\\n\\n- IOC (Indicators of Compromise) analysis\\n- Threat actor profiling\\n- Malware analysis and attribution\\n- OSINT gathering for security research\\n- CVE research and vulnerability intelligence\\n\\nProvide detailed, actionable threat intelligence with proper attribution and confidence levels.',
                expertise: 'threat intelligence and IOC analysis',
                keywords: 'threat, intel, ioc, indicator, malware, apt, vulnerability, cve, osint, attribution',
                patterns: 'CVE-\\\\d{{4}}-\\\\d+, \\\\b(IOC|indicator|threat)\\\\b',
                examples: 'What are the latest threat indicators for APT29?\\nAnalyze this hash: a1b2c3d4e5f6\\nShow me recent CVEs for Apache'
            }},
            securityRouter: {{
                type: 'router',
                language: 'python',
                name: 'Security Operations Router',
                domain: 'security.yourdomain.com',
                description: 'Central router for security operations that coordinates threat intel, incident response, and compliance specialists',
                systemPrompt: 'You are a security operations coordinator that routes security questions to appropriate specialists. You coordinate:\\n\\n- Threat intelligence analysis\\n- Incident response procedures\\n- Compliance and audit requirements\\n- Vulnerability management\\n\\nRoute questions to the most appropriate specialist or provide general security guidance.',
                examples: 'Investigate this security alert\\nWhat are our compliance requirements?\\nAnalyze this potential threat'
            }},
            codeAnalyst: {{
                type: 'specialist',
                language: 'javascript',
                name: 'Code Security Analyst',
                domain: 'code-security.yourdomain.com',
                description: 'JavaScript-powered specialist for code vulnerability analysis and security reviews',
                systemPrompt: 'You are a code security expert specializing in:\\n\\n- Static code analysis\\n- Vulnerability identification\\n- Security code review\\n- OWASP compliance\\n- Secure coding practices\\n\\nProvide detailed security analysis with specific remediation recommendations.',
                expertise: 'code security analysis',
                keywords: 'code, vulnerability, security, owasp, injection, xss, csrf, analysis',
                patterns: '(SQL|XSS|CSRF|injection)',
                examples: 'Review this code for security issues\\nCheck for SQL injection vulnerabilities\\nAnalyze OWASP compliance'
            }},
            financeExpert: {{
                type: 'specialist',
                language: 'python',
                name: 'Financial Analysis Expert',
                domain: 'finance.yourdomain.com',
                description: 'Python-powered specialist for financial data analysis and investment insights',
                systemPrompt: 'You are a financial analysis expert specializing in:\\n\\n- Market analysis and trends\\n- Investment research\\n- Financial modeling\\n- Risk assessment\\n- Economic indicators\\n\\nProvide data-driven financial insights with proper disclaimers.',
                expertise: 'financial analysis and investment research',
                keywords: 'finance, investment, market, analysis, portfolio, risk, economics',
                patterns: '\\\\$[0-9,]+|\\\\b(USD|EUR|GBP)\\\\b',
                examples: 'Analyze the current market trends\\nWhat are the risks in this portfolio?\\nExplain this financial metric'
            }}
        }};

        function switchTab(tabName) {{
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => {{
                content.classList.remove('active');
            }});

            // Remove active class from all tabs
            document.querySelectorAll('.tab').forEach(tab => {{
                tab.classList.remove('active');
            }});

            // Show selected tab content
            document.getElementById(tabName).classList.add('active');

            // Add active class to selected tab
            event.target.classList.add('active');
        }}

        function loadExample(exampleKey) {{
            const example = examples[exampleKey];
            if (!example) return;

            // Switch to generator tab
            switchTab('generator');
            document.querySelector('.tab').click();

            // Fill form fields
            Object.keys(example).forEach(key => {{
                const field = document.getElementById(key);
                if (field) {{
                    field.value = example[key];
                    if (key === 'type') {{
                        toggleSpecialistFields();
                    }}
                }}
            }});

            // Handle examples array
            if (example.examples) {{
                document.getElementById('examples').value = example.examples.replace(/\\\\n/g, '\\n');
            }}
        }}

        function toggleSpecialistFields() {{
            const agentType = document.getElementById('agentType').value;
            const specialistFields = document.getElementById('specialistFields');

            if (agentType === 'specialist') {{
                specialistFields.style.display = 'block';
            }} else {{
                specialistFields.style.display = 'none';
            }}
        }}

        function showResult(message, type) {{
            const result = document.getElementById('result');
            result.className = `result ${{type}}`;
            result.innerHTML = message;
            result.style.display = 'block';
            result.scrollIntoView({{ behavior: 'smooth' }});
        }}

        async function validateConfig() {{
            const formData = new FormData(document.getElementById('agentForm'));
            const config = Object.fromEntries(formData);

            // Process arrays
            if (config.keywords) {{
                config.keywords = config.keywords.split(',').map(k => k.trim()).filter(k => k);
            }}
            if (config.patterns) {{
                config.patterns = config.patterns.split(',').map(p => p.trim()).filter(p => p);
            }}
            if (config.examples) {{
                config.examples = config.examples.split('\\n').map(e => e.trim()).filter(e => e);
            }}

            showResult('🔍 Validating configuration...', 'loading');

            try {{
                const response = await fetch('/mcp', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        method: 'validate_config',
                        params: {{ config, language: config.language }}
                    }})
                }});

                const result = await response.json();

                if (result.valid) {{
                    showResult(`✅ Configuration is valid!<br><strong>Worker name:</strong> ${{result.worker_name}}`, 'success');
                }} else {{
                    showResult(`❌ Configuration error: ${{result.error}}`, 'error');
                }}
            }} catch (error) {{
                showResult(`❌ Validation failed: ${{error.message}}`, 'error');
            }}
        }}

        async function generateAgent(event) {{
            event.preventDefault();

            const formData = new FormData(event.target);
            const config = Object.fromEntries(formData);
            const language = config.language;
            delete config.language;

            // Process arrays
            if (config.keywords) {{
                config.keywords = config.keywords.split(',').map(k => k.trim()).filter(k => k);
            }}
            if (config.patterns) {{
                config.patterns = config.patterns.split(',').map(p => p.trim()).filter(p => p);
            }}
            if (config.examples) {{
                config.examples = config.examples.split('\\n').map(e => e.trim()).filter(e => e);
            }}

            showResult('🏭 Generating agent and committing to GitHub...', 'loading');

            try {{
                const response = await fetch('/mcp', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        method: 'generate_agent',
                        params: {{ config, language }}
                    }})
                }});

                const result = await response.json();

                if (result.success) {{
                    let message = `✅ <strong>${{result.agent_name}}</strong> generated successfully!<br><br>`;
                    message += `<strong>🌐 Domain:</strong> ${{result.domain}}<br>`;
                    message += `<strong>🔧 Worker:</strong> ${{result.worker_name}}<br>`;
                    message += `<strong>📁 Language:</strong> ${{result.language}}<br><br>`;
                    message += `<strong>📋 Next Steps:</strong><br>`;
                    result.next_steps.forEach(step => {{
                        message += `• ${{step}}<br>`;
                    }});

                    if (result.github && result.github.pr_url) {{
                        message += `<br><a href="${{result.github.pr_url}}" target="_blank" style="color: #667eea; text-decoration: none;">🔗 View Pull Request</a>`;
                    }}

                    showResult(message, 'success');
                }} else {{
                    showResult(`❌ Generation failed: ${{result.error}}<br><br>${{result.suggestion || ''}}`, 'error');
                }}
            }} catch (error) {{
                showResult(`❌ Request failed: ${{error.message}}`, 'error');
            }}
        }}

        // Event listeners
        document.getElementById('agentType').addEventListener('change', toggleSpecialistFields);
        document.getElementById('agentForm').addEventListener('submit', generateAgent);

        // Initialize
        toggleSpecialistFields();
    </script>
</body>
</html>
"""
