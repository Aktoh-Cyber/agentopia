.PHONY: help test clean push validate

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

test: ## Test template generation
	@echo "Testing JavaScript workflow supervisor cookiecutter template..."
	@rm -rf test-output
	@cookiecutter . --no-input --output-dir test-output \
		-f project_name="Test Workflow Supervisor" \
		-f domain="workflow.example.com" \
		-f supervisor_strategy="sequential" \
		-f error_handling="retry_with_fallback" \
		-f workflow_steps_json='[{"name":"analyze","description":"Analyze request","agent":"analyst"},{"name":"process","description":"Process data","agent":"processor"}]' \
		-f specialist_agents_json='[{"name":"analyst","endpoint":"https://analyst.example.com","description":"Analyzes"},{"name":"processor","endpoint":"https://processor.example.com","description":"Processes"}]'
	@echo "✅ Template generated successfully"
	@cd test-output/test-workflow-supervisor && npm install
	@echo "✅ Dependencies installed successfully"
	@echo "✅ JavaScript workflow supervisor template test completed!"

validate: ## Validate cookiecutter.json
	@python -m json.tool cookiecutter.json > /dev/null
	@echo "✅ cookiecutter.json is valid"

clean: ## Remove test artifacts
	@rm -rf test-output
	@echo "✅ Cleaned test artifacts"

push: ## Push to GitHub
	@git add .
	@git commit -m "Update JavaScript workflow supervisor template" || true
	@git push origin main
	@echo "✅ Pushed to GitHub"