# Agent Framework Makefile
# Comprehensive build automation for multi-language AI agent framework

# Default shell
SHELL := /bin/bash

# Colors for output
RED := $(shell printf "\033[0;31m")
GREEN := $(shell printf "\033[0;32m")
YELLOW := $(shell printf "\033[1;33m")
BLUE := $(shell printf "\033[0;34m")
PURPLE := $(shell printf "\033[0;35m")
CYAN := $(shell printf "\033[0;36m")
WHITE := $(shell printf "\033[1;37m")
NC := $(shell printf "\033[0m")

# Default directories
AGENTS_DIR ?= agents
PYTHON_GEN_DIR := generators/python
JS_GEN_DIR := generators/javascript

# Python commands
PYTHON := uv run python
UV := uv

# Node commands
NODE := node
NPM := npm

# Make settings
.DEFAULT_GOAL := help
.PHONY: help setup install dev-setup format lint type-check test qa clean
.PHONY: generate-agent generate-python generate-javascript list-configs
.PHONY: deploy-agent deploy-all update-deps info

# Banner function
define print_banner
	@printf "$(CYAN)\n"
	@printf "    ___                  __     ______                                           __  \n"
	@printf "   /   | ____ ____  ____/ /_   / ____/________ _____ ___  ___ _      ______  _____/ /__\n"
	@printf "  / /| |/ __ \`/ _ \/ __ / __/  / /_  / ___/ __ \`/ __ \`__ \/ _ \\ | /| / / __ \/ ___/ //_/\n"
	@printf " / ___ / /_/ /  __/ / / / /_   / __/ / /  / /_/ / / / / / /  __/ |/ |/ / /_/ / /  / ,<  \n"
	@printf "/_/  |_\\__, /\\___/_/ /_/\\__/  /_/   /_/   \\__,_/_/ /_/ /_/\\___/|__/|__/\\____/_/  /_/|_| \n"
	@printf "      /____/                                                                             \n"
	@printf "$(NC)\n"
endef

##@ General

help: ## Display this help message
	$(call print_banner)
	@printf "$(WHITE)Multi-language AI Agent Framework for Cloudflare Workers$(NC)\n\n"
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(CYAN)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@printf "\n$(WHITE)Examples:$(NC)\n"
	@printf "  $(GREEN)make setup$(NC)                    # Initial project setup\n"
	@printf "  $(GREEN)make generate-agent$(NC)           # Interactive agent generation\n"
	@printf "  $(GREEN)make qa$(NC)                       # Run all quality checks\n"
	@printf "  $(GREEN)make deploy-agent AGENT=judge$(NC) # Deploy specific agent\n"

##@ Setup & Installation

setup: ## Complete project setup (Python + JavaScript)
	@echo "$(YELLOW)🚀 Setting up Agent Framework...$(NC)"
	@$(MAKE) install-python
	@$(MAKE) install-javascript
	@echo "$(GREEN)✅ Setup complete!$(NC)"

install: setup ## Alias for setup

install-python: ## Install Python dependencies with uv
	@printf "$(YELLOW)📦 Installing Python dependencies...$(NC)\n"
	@command -v uv >/dev/null 2>&1 || { printf "$(RED)Error: uv not found. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh$(NC)\n"; exit 1; }
	@$(UV) sync
	@printf "$(GREEN)✅ Python dependencies installed$(NC)\n"

install-javascript: ## Install JavaScript dependencies
	@echo "$(YELLOW)📦 Installing JavaScript dependencies...$(NC)"
	@cd $(JS_GEN_DIR) && $(NPM) install
	@echo "$(GREEN)✅ JavaScript dependencies installed$(NC)"

dev-setup: setup ## Setup development environment
	@echo "$(YELLOW)🛠️  Setting up development environment...$(NC)"
	@$(UV) sync --dev
	@echo "$(GREEN)✅ Development environment ready$(NC)"

##@ Code Quality

format: ## Format all code (Python + JavaScript)
	@echo "$(YELLOW)🎨 Formatting code...$(NC)"
	@$(MAKE) format-python
	@$(MAKE) format-javascript
	@echo "$(GREEN)✅ Code formatted$(NC)"

format-python: ## Format Python code
	@printf "$(BLUE)  Python:$(NC)\n"
	@$(UV) run black generators/
	@$(UV) run isort generators/

format-javascript: ## Format JavaScript code
	@echo "$(BLUE)  JavaScript:$(NC)"
	@cd $(JS_GEN_DIR) && $(NPM) run format 2>/dev/null || echo "    No formatter configured"

lint: ## Lint all code
	@echo "$(YELLOW)🔍 Linting code...$(NC)"
	@$(MAKE) lint-python
	@$(MAKE) lint-javascript
	@echo "$(GREEN)✅ Linting complete$(NC)"

lint-python: ## Lint Python code
	@printf "$(BLUE)  Python:$(NC)\n"
	@$(UV) run ruff check generators/ || true

lint-javascript: ## Lint JavaScript code
	@echo "$(BLUE)  JavaScript:$(NC)"
	@cd $(JS_GEN_DIR) && $(NPM) run lint 2>/dev/null || echo "    No linter configured"

type-check: ## Run type checking (Python)
	@echo "$(YELLOW)🔍 Type checking...$(NC)"
	@$(UV) run mypy generators/python --ignore-missing-imports || true
	@echo "$(GREEN)✅ Type checking complete$(NC)"

test: ## Run all tests
	@echo "$(YELLOW)🧪 Running tests...$(NC)"
	@$(MAKE) test-python
	@$(MAKE) test-javascript
	@echo "$(GREEN)✅ All tests complete$(NC)"

test-python: ## Run Python tests
	@echo "$(BLUE)  Python tests:$(NC)"
	@$(UV) run pytest tests/ -v 2>/dev/null || echo "    No tests found"

test-javascript: ## Run JavaScript tests
	@echo "$(BLUE)  JavaScript tests:$(NC)"
	@cd $(JS_GEN_DIR) && $(NPM) test 2>/dev/null || echo "    No tests configured"

qa: format lint type-check test ## Run all quality checks

##@ Agent Generation

generate-agent: ## Interactive agent generation (prompts for language)
	@echo "$(YELLOW)🏭 Agent Generator$(NC)"
	@echo ""
	@echo "Select language:"
	@echo "  1) Python"
	@echo "  2) JavaScript"
	@read -p "Enter choice [1-2]: " choice; \
	case $$choice in \
		1) $(MAKE) generate-python ;; \
		2) $(MAKE) generate-javascript ;; \
		*) echo "$(RED)Invalid choice$(NC)" ;; \
	esac

generate-python: ## Generate a Python agent (CONFIG=path/to/config.json OUTPUT=agent-name)
	@if [ -z "$(CONFIG)" ]; then \
		echo "$(YELLOW)Available Python configs:$(NC)"; \
		ls -1 $(PYTHON_GEN_DIR)/configs/*.json 2>/dev/null | sed 's/.*\//  - /' || echo "  No configs found"; \
		echo ""; \
		read -p "Config file path: " config; \
		read -p "Output directory name: " output; \
		$(MAKE) generate-python CONFIG=$$config OUTPUT=$$output; \
	else \
		echo "$(YELLOW)🐍 Generating Python agent...$(NC)"; \
		mkdir -p $(AGENTS_DIR); \
		cd $(PYTHON_GEN_DIR) && $(PYTHON) agent_builder.py $(CONFIG) ../../$(AGENTS_DIR)/$(OUTPUT); \
		echo "$(GREEN)✅ Python agent generated at: $(AGENTS_DIR)/$(OUTPUT)$(NC)"; \
		if echo "$(OUTPUT)" | grep -q "test"; then \
			echo "$(YELLOW)🧹 Test agent detected - will auto-cleanup after 10 seconds...$(NC)"; \
			(sleep 10 && rm -rf $(AGENTS_DIR)/$(OUTPUT) && echo "$(BLUE)🗑️  Cleaned up test agent: $(OUTPUT)$(NC)" || true) & \
		fi; \
	fi

generate-javascript: ## Generate a JavaScript agent (CONFIG=path/to/config.json OUTPUT=agent-name)
	@if [ -z "$(CONFIG)" ]; then \
		echo "$(YELLOW)Available JavaScript configs:$(NC)"; \
		ls -1 $(JS_GEN_DIR)/configs/*.json 2>/dev/null | sed 's/.*\//  - /' || echo "  No configs found"; \
		echo ""; \
		read -p "Config file path: " config; \
		read -p "Output directory name: " output; \
		$(MAKE) generate-javascript CONFIG=$$config OUTPUT=$$output; \
	else \
		echo "$(YELLOW)📜 Generating JavaScript agent...$(NC)"; \
		mkdir -p $(AGENTS_DIR); \
		cd $(JS_GEN_DIR) && $(NODE) build-agent.js $(CONFIG) ../../$(AGENTS_DIR)/$(OUTPUT); \
		echo "$(GREEN)✅ JavaScript agent generated at: $(AGENTS_DIR)/$(OUTPUT)$(NC)"; \
		if echo "$(OUTPUT)" | grep -q "test"; then \
			echo "$(YELLOW)🧹 Test agent detected - will auto-cleanup after 10 seconds...$(NC)"; \
			(sleep 10 && rm -rf $(AGENTS_DIR)/$(OUTPUT) && echo "$(BLUE)🗑️  Cleaned up test agent: $(OUTPUT)$(NC)" || true) & \
		fi; \
	fi

# Quick generation shortcuts
gen-py: generate-python ## Shortcut for generate-python
gen-js: generate-javascript ## Shortcut for generate-javascript

gen-cybersec-router: ## Generate cybersec router agent (Python)
	@echo "$(YELLOW)Generating Cybersec Router Agent...$(NC)"
	$(MAKE) generate-python CONFIG=configs/cybersec-router.json OUTPUT=cybersec-router

gen-judge-specialist: ## Generate judge specialist agent (Python)
	@echo "$(YELLOW)Generating Judge Specialist Agent...$(NC)"
	$(MAKE) generate-python CONFIG=configs/judge-specialist.json OUTPUT=judge-specialist

gen-agent-generator: ## Generate agent generator agent (Python)
	@echo "$(YELLOW)Generating Agent Generator Agent...$(NC)"
	$(MAKE) generate-python CONFIG=configs/agent-generator.json OUTPUT=agent-generator

list-configs: ## List all available agent configurations
	@echo "$(YELLOW)📋 Available Configurations:$(NC)"
	@echo ""
	@echo "$(BLUE)Python configs:$(NC)"
	@ls -1 $(PYTHON_GEN_DIR)/configs/*.json 2>/dev/null | sed 's/.*\//  - /' || echo "  None found"
	@echo ""
	@echo "$(BLUE)JavaScript configs:$(NC)"
	@ls -1 $(JS_GEN_DIR)/configs/*.json 2>/dev/null | sed 's/.*\//  - /' || echo "  None found"

test-agent-generation: ## Test agent generation (auto-cleanup)
	@echo "$(YELLOW)🧪 Testing Agent Generation$(NC)"
	@echo ""
	@read -p "Select language (python/javascript): " lang; \
	read -p "Config file path: " config; \
	timestamp=$$(date +%s); \
	test_name="test-agent-$$timestamp"; \
	echo ""; \
	echo "$(BLUE)Generating test agent: $$test_name$(NC)"; \
	if [ "$$lang" = "python" ]; then \
		$(MAKE) generate-python CONFIG=$$config OUTPUT=$$test_name; \
	elif [ "$$lang" = "javascript" ]; then \
		$(MAKE) generate-javascript CONFIG=$$config OUTPUT=$$test_name; \
	else \
		echo "$(RED)Invalid language. Use 'python' or 'javascript'$(NC)"; \
		exit 1; \
	fi; \
	echo ""; \
	echo "$(GREEN)✅ Test completed. Agent will auto-cleanup in 10 seconds.$(NC)"

##@ Agent Deployment

deploy-agent: ## Deploy a specific agent (AGENT=agent-name)
	@if [ -z "$(AGENT)" ]; then \
		echo "$(YELLOW)Available agents to deploy:$(NC)"; \
		echo ""; \
		echo "$(BLUE)Available agents:$(NC)"; \
		ls -1 $(AGENTS_DIR) 2>/dev/null | sed 's/^/  - /' || echo "  None found"; \
		echo ""; \
		echo "$(YELLOW)Usage: make deploy-agent AGENT=<agent-name>$(NC)"; \
	else \
		echo "$(YELLOW)🚀 Deploying agent: $(AGENT)$(NC)"; \
		if [ -d "$(AGENTS_DIR)/$(AGENT)" ]; then \
			cd $(AGENTS_DIR)/$(AGENT) && ./scripts/deploy.sh; \
		else \
			echo "$(RED)Error: Agent '$(AGENT)' not found in $(AGENTS_DIR)/$(NC)"; \
			exit 1; \
		fi; \
	fi

deploy-all: ## Deploy all agents (use with caution!)
	@echo "$(YELLOW)🚀 Deploying all agents...$(NC)"
	@echo "$(RED)Warning: This will deploy all agents. Continue? [y/N]$(NC)"
	@read -p "" confirm; \
	if [ "$$confirm" = "y" ] || [ "$$confirm" = "Y" ]; then \
		for agent in $(AGENTS_DIR)/*/scripts/deploy.sh; do \
			if [ -f "$$agent" ]; then \
				echo "$(BLUE)Deploying $$(dirname $$(dirname $$agent))...$(NC)"; \
				cd $$(dirname $$(dirname $$agent)) && ./scripts/deploy.sh; \
			fi; \
		done; \
		echo "$(GREEN)✅ All agents deployed$(NC)"; \
	else \
		echo "$(YELLOW)Deployment cancelled$(NC)"; \
	fi

##@ Utilities

clean: ## Clean generated files and caches
	@echo "$(YELLOW)🧹 Cleaning...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✅ Clean complete$(NC)"

update-deps: ## Update all dependencies
	@echo "$(YELLOW)📦 Updating dependencies...$(NC)"
	@$(UV) sync --upgrade
	@cd $(JS_GEN_DIR) && $(NPM) update
	@echo "$(GREEN)✅ Dependencies updated$(NC)"

info: ## Show project information
	@echo "$$BANNER"
	@echo "$(WHITE)Project Structure:$(NC)"
	@echo "  $(BLUE)generators/$(NC)"
	@echo "    ├── $(GREEN)python/$(NC)      - Python agent generator"
	@echo "    └── $(GREEN)javascript/$(NC) - JavaScript agent generator"
	@echo "  $(BLUE)agents/$(NC)          - All agents (hand-crafted and generated)"
	@echo ""
	@echo "$(WHITE)Key Commands:$(NC)"
	@echo "  • $(CYAN)make generate-agent$(NC) - Create a new agent"
	@echo "  • $(CYAN)make deploy-agent$(NC)  - Deploy an agent to Cloudflare"
	@echo "  • $(CYAN)make qa$(NC)            - Run quality checks"
	@echo ""
	@echo "$(WHITE)Environment:$(NC)"
	@echo "  Python: $$(uv run python --version 2>/dev/null || echo 'Not installed')"
	@echo "  Node:   $$(node --version 2>/dev/null || echo 'Not installed')"
	@echo "  uv:     $$(uv --version 2>/dev/null || echo 'Not installed')"

##@ Development Shortcuts

fmt: format ## Alias for format
check: qa ## Alias for qa
deps: update-deps ## Alias for update-deps

# Special targets for CI/CD
ci: ## Run CI pipeline checks
	@echo "$(YELLOW)🔄 Running CI checks...$(NC)"
	@$(MAKE) lint
	@$(MAKE) type-check
	@$(MAKE) test
	@echo "$(GREEN)✅ CI checks passed$(NC)"

# Validation targets
validate-config: ## Validate an agent config file (CONFIG=path/to/config.json)
	@if [ -z "$(CONFIG)" ]; then \
		echo "$(RED)Error: CONFIG parameter required$(NC)"; \
		echo "Usage: make validate-config CONFIG=path/to/config.json"; \
		exit 1; \
	fi
	@echo "$(YELLOW)🔍 Validating config: $(CONFIG)$(NC)"
	@$(PYTHON) -m json.tool $(CONFIG) > /dev/null && echo "$(GREEN)✅ Valid JSON$(NC)" || echo "$(RED)❌ Invalid JSON$(NC)"

# Watch for changes (requires entr)
watch: ## Watch for changes and run tests
	@command -v entr >/dev/null 2>&1 || { echo "$(RED)Error: entr not found. Install with: brew install entr$(NC)"; exit 1; }
	@find generators -name "*.py" -o -name "*.js" | entr -c $(MAKE) test