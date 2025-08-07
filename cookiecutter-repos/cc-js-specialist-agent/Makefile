.PHONY: help test clean push validate

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

test: ## Test template generation
	@echo "Testing cookiecutter template..."
	@rm -rf test-output
	@cookiecutter . --no-input --output-dir test-output \
		-f project_name="Test Specialist Agent" \
		-f domain="test-specialist.example.com" \
		-f mcp_tool_name="test_specialist" \
		-f expertise="Testing and validation" \
		-f keywords_json='["test", "validate", "check"]' \
		-f patterns_json='["test.*", "validate.*"]'
	@echo "✅ Template generated successfully"
	@cd test-output/* && npm install
	@echo "✅ Dependencies installed successfully"
	@echo "Test completed! Check test-output directory"

validate: ## Validate cookiecutter.json
	@python -m json.tool cookiecutter.json > /dev/null
	@echo "✅ cookiecutter.json is valid"

clean: ## Remove test artifacts
	@rm -rf test-output
	@echo "✅ Cleaned test artifacts"

push: ## Push to GitHub
	@git add .
	@git commit -m "Update specialist agent template" || true
	@git push origin main
	@echo "✅ Pushed to GitHub"