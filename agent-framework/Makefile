.PHONY: help install install-dev format lint type-check test clean generate-js generate-py deploy-agent
.DEFAULT_GOAL := help

# Colors for output
CYAN = \033[0;36m
GREEN = \033[0;32m
YELLOW = \033[0;33m
RED = \033[0;31m
NC = \033[0m # No Color

help: ## Show this help message
	@echo "$(CYAN)Agent Framework Development Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "install|setup" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Development:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "format|lint|type|test" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Agent Generation:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "generate|deploy" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Maintenance:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -E "clean|update" | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(CYAN)%-20s$(NC) %s\n", $$1, $$2}'

install: ## Install production dependencies
	@echo "$(YELLOW)Installing production dependencies...$(NC)"
	uv sync --no-dev

install-dev: ## Install development dependencies
	@echo "$(YELLOW)Installing development dependencies...$(NC)"
	uv sync

format: ## Format code with black and isort
	@echo "$(YELLOW)Formatting Python code...$(NC)"
	uv run black generators/
	uv run isort generators/

lint: ## Run linting with ruff
	@echo "$(YELLOW)Running linting...$(NC)"
	uv run ruff check generators/

type-check: ## Run type checking with mypy
	@echo "$(YELLOW)Running type checking...$(NC)"
	uv run mypy generators/

test: ## Run tests
	@echo "$(YELLOW)Running tests...$(NC)"
	uv run pytest

clean: ## Clean up build artifacts and caches
	@echo "$(YELLOW)Cleaning up...$(NC)"
	rm -rf .venv/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/
	rm -rf .ruff_cache/
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete

# Agent Generation Commands
generate-js: ## Generate JavaScript agent (usage: make generate-js CONFIG=configs/example.json OUTPUT=../output)
	@if [ -z "$(CONFIG)" ] || [ -z "$(OUTPUT)" ]; then \
		echo "$(RED)Error: CONFIG and OUTPUT parameters required$(NC)"; \
		echo "$(YELLOW)Usage: make generate-js CONFIG=generators/javascript/configs/example.json OUTPUT=../my-agent$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Generating JavaScript agent...$(NC)"
	cd generators/javascript && node build-agent.js $(CONFIG) $(OUTPUT)

generate-py: ## Generate Python agent (usage: make generate-py CONFIG=configs/example.json OUTPUT=../output)
	@if [ -z "$(CONFIG)" ] || [ -z "$(OUTPUT)" ]; then \
		echo "$(RED)Error: CONFIG and OUTPUT parameters required$(NC)"; \
		echo "$(YELLOW)Usage: make generate-py CONFIG=generators/python/configs/example.json OUTPUT=../my-agent$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Generating Python agent...$(NC)"
	cd generators/python && uv run python agent_builder.py $(CONFIG) $(OUTPUT)

# Quick generation shortcuts
gen-cybersec-router: ## Generate cybersec router agent (Python)
	@echo "$(YELLOW)Generating Cybersec Router Agent...$(NC)"
	$(MAKE) generate-py CONFIG=generators/python/configs/cybersec-router.json OUTPUT=agents/cybersec-router-new

gen-judge-specialist: ## Generate judge specialist agent (Python)
	@echo "$(YELLOW)Generating Judge Specialist Agent...$(NC)"
	$(MAKE) generate-py CONFIG=generators/python/configs/judge-specialist.json OUTPUT=agents/judge-specialist-new

gen-agent-generator: ## Generate agent generator agent (Python)
	@echo "$(YELLOW)Generating Agent Generator Agent...$(NC)"
	$(MAKE) generate-py CONFIG=generators/python/configs/agent-generator.json OUTPUT=agents/agent-generator-new

deploy-agent: ## Deploy agent (usage: make deploy-agent AGENT=agents/my-agent)
	@if [ -z "$(AGENT)" ]; then \
		echo "$(RED)Error: AGENT parameter required$(NC)"; \
		echo "$(YELLOW)Usage: make deploy-agent AGENT=agents/my-agent$(NC)"; \
		exit 1; \
	fi
	@if [ ! -d "$(AGENT)" ]; then \
		echo "$(RED)Error: Agent directory $(AGENT) does not exist$(NC)"; \
		exit 1; \
	fi
	@echo "$(YELLOW)Deploying agent from $(AGENT)...$(NC)"
	cd $(AGENT) && ./scripts/deploy.sh

# Development workflow
dev-setup: install-dev ## Complete development setup
	@echo "$(GREEN)Development environment ready!$(NC)"
	@echo "$(YELLOW)Next steps:$(NC)"
	@echo "  1. Configure your Cloudflare credentials"
	@echo "  2. Generate an agent: make gen-cybersec-router"
	@echo "  3. Deploy it: make deploy-agent AGENT=agents/cybersec-router-new"

# Quality checks
qa: format lint type-check test ## Run all quality assurance checks
	@echo "$(GREEN)All quality checks passed!$(NC)"

# Update dependencies
update: ## Update dependencies
	@echo "$(YELLOW)Updating dependencies...$(NC)"
	uv sync --upgrade

# Show project info
info: ## Show project information
	@echo "$(CYAN)Agent Framework v2.0$(NC)"
	@echo ""
	@echo "$(GREEN)Project Structure:$(NC)"
	@echo "  generators/          - Code generators (JS & Python)"
	@echo "  generated-agents/    - Auto-generated agents (GitOps)"
	@echo "  agents/              - Manual agents and examples"
	@echo "  .github/workflows/   - CI/CD automation"
	@echo ""
	@echo "$(GREEN)Key Files:$(NC)"
	@echo "  pyproject.toml       - Python project configuration"
	@echo "  Makefile             - Development commands"
	@echo "  CLAUDE.md            - AI assistant guidance"
	@echo ""
	@echo "$(GREEN)Dependencies:$(NC)"
	@uv tree --depth 1