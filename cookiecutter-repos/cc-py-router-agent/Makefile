.PHONY: help test clean push validate

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

test: ## Test template generation
	@echo "Testing Python router cookiecutter template..."
	@rm -rf test-output
	@cookiecutter . --no-input --output-dir test-output \
		-f project_name="Test Python Router" \
		-f domain="test-router.example.com" \
		-f registry_json='{"tools": []}'
	@echo "✅ Template generated successfully"
	@echo "✅ Python router template test completed!"
	@echo "Note: Python dependencies not installed (production uses standard library only)"

validate: ## Validate cookiecutter.json
	@python -m json.tool cookiecutter.json > /dev/null
	@echo "✅ cookiecutter.json is valid"

clean: ## Remove test artifacts
	@rm -rf test-output
	@echo "✅ Cleaned test artifacts"

push: ## Push to GitHub
	@git add .
	@git commit -m "Update Python router agent template" || true
	@git push origin main
	@echo "✅ Pushed to GitHub"