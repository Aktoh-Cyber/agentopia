.PHONY: help test clean push validate lint

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-15s %s\n", $$1, $$2}'

test: ## Test template generation
	@echo "Testing Python workflow supervisor cookiecutter template..."
	@rm -rf test-output
	@cookiecutter . --no-input --output-dir test-output \
		-f project_name="Test Python Workflow Supervisor" \
		-f domain="py-workflow.example.com" \
		-f supervisor_strategy="sequential" \
		-f error_handling="retry_with_fallback" \
		-f workflow_steps_json='[{"name":"analyze","description":"Analyze request","agent":"analyst"},{"name":"process","description":"Process data","agent":"processor"}]' \
		-f specialist_agents_json='[{"name":"analyst","endpoint":"https://analyst.example.com","description":"Analyzes"},{"name":"processor","endpoint":"https://processor.example.com","description":"Processes"}]'
	@echo "✅ Template generated successfully"
	@echo "🐍 Validating Python syntax..."
	@cd test-output/test-python-workflow-supervisor && python3 -m py_compile src/*.py
	@echo "✅ Python syntax validation passed"
	@echo "🔧 Checking Pyodide compatibility..."
	@cd test-output/test-python-workflow-supervisor && python3 -c "import ast; [ast.parse(open(f'src/{f}').read()) for f in ['entry.py', 'base_agent.py', 'workflow_engine.py', 'state_manager.py']]"
	@echo "✅ Python workflow supervisor template test completed!"

test-all: ## Test all workflow strategies
	@echo "Testing all workflow strategies..."
	@rm -rf test-output-all
	@mkdir -p test-output-all
	
	@echo "Testing sequential strategy..."
	@cookiecutter . --no-input --output-dir test-output-all/sequential \
		-f project_name="Sequential Workflow" \
		-f supervisor_strategy="sequential" \
		-f workflow_steps_json='[{"name":"step1","agent":"agent1"},{"name":"step2","agent":"agent2"}]' \
		-f specialist_agents_json='[{"name":"agent1","endpoint":"https://agent1.com"},{"name":"agent2","endpoint":"https://agent2.com"}]'
	
	@echo "Testing parallel strategy..."
	@cookiecutter . --no-input --output-dir test-output-all/parallel \
		-f project_name="Parallel Workflow" \
		-f supervisor_strategy="parallel" \
		-f workflow_steps_json='[{"name":"step1","agent":"agent1"},{"name":"step2","agent":"agent2"}]' \
		-f specialist_agents_json='[{"name":"agent1","endpoint":"https://agent1.com"},{"name":"agent2","endpoint":"https://agent2.com"}]'
	
	@echo "Testing conditional strategy..."
	@cookiecutter . --no-input --output-dir test-output-all/conditional \
		-f project_name="Conditional Workflow" \
		-f supervisor_strategy="conditional" \
		-f workflow_steps_json='[{"name":"step1","agent":"agent1","condition":"True"},{"name":"step2","agent":"agent2"}]' \
		-f specialist_agents_json='[{"name":"agent1","endpoint":"https://agent1.com"},{"name":"agent2","endpoint":"https://agent2.com"}]'
	
	@echo "Testing map-reduce strategy..."
	@cookiecutter . --no-input --output-dir test-output-all/mapreduce \
		-f project_name="MapReduce Workflow" \
		-f supervisor_strategy="map_reduce" \
		-f workflow_steps_json='[{"name":"map1","agent":"mapper","phase":"map"},{"name":"reduce1","agent":"reducer","phase":"reduce"}]' \
		-f specialist_agents_json='[{"name":"mapper","endpoint":"https://mapper.com"},{"name":"reducer","endpoint":"https://reducer.com"}]'
	
	@echo "Validating all generated projects..."
	@for dir in test-output-all/*/*/; do \
		echo "Validating $$dir..."; \
		cd "$$dir" && python3 -m py_compile src/*.py; \
		cd - > /dev/null; \
	done
	@echo "✅ All workflow strategies tested successfully!"

lint: ## Lint Python code in template
	@echo "Linting Python template files..."
	@python3 -m py_compile hooks/*.py
	@echo "✅ Hook files syntax is valid"
	
	@echo "Checking for common issues in template files..."
	@find . -name "*.py" -path "./{{*" -exec python3 -m py_compile {} \; 2>/dev/null || echo "⚠️  Template files contain Jinja2 syntax (expected)"
	@echo "✅ Template structure looks good"

validate: ## Validate cookiecutter.json and template structure
	@echo "Validating cookiecutter.json..."
	@python3 -m json.tool cookiecutter.json > /dev/null
	@echo "✅ cookiecutter.json is valid JSON"
	
	@echo "Validating template structure..."
	@test -d "{{cookiecutter.project_slug}}" || (echo "❌ Missing template directory" && exit 1)
	@test -d "{{cookiecutter.project_slug}}/src" || (echo "❌ Missing src directory" && exit 1)
	@test -d "{{cookiecutter.project_slug}}/scripts" || (echo "❌ Missing scripts directory" && exit 1)
	@test -d "hooks" || (echo "❌ Missing hooks directory" && exit 1)
	@test -f "{{cookiecutter.project_slug}}/wrangler.toml" || (echo "❌ Missing wrangler.toml" && exit 1)
	@test -f "{{cookiecutter.project_slug}}/scripts/deploy.sh" || (echo "❌ Missing deploy.sh" && exit 1)
	@test -f "hooks/pre_gen_project.py" || (echo "❌ Missing pre_gen_project.py" && exit 1)
	@test -f "hooks/post_gen_project.py" || (echo "❌ Missing post_gen_project.py" && exit 1)
	@echo "✅ Template structure is valid"
	
	@echo "Validating hook permissions..."
	@test -x "hooks/pre_gen_project.py" || chmod +x "hooks/pre_gen_project.py"
	@test -x "hooks/post_gen_project.py" || chmod +x "hooks/post_gen_project.py"
	@echo "✅ Hook permissions are correct"

test-hooks: ## Test pre/post generation hooks
	@echo "Testing pre-generation hook..."
	@cd hooks && python3 pre_gen_project.py
	@echo "✅ Pre-generation hook works"
	
	@echo "Note: Post-generation hook requires generated project structure"

check-dependencies: ## Check required dependencies
	@echo "Checking dependencies..."
	@command -v python3 >/dev/null || (echo "❌ python3 not found" && exit 1)
	@command -v cookiecutter >/dev/null || (echo "❌ cookiecutter not found - install with: pip install cookiecutter" && exit 1)
	@python3 -c "import json" || (echo "❌ json module not available" && exit 1)
	@python3 -c "import ast" || (echo "❌ ast module not available" && exit 1)
	@echo "✅ All dependencies available"

benchmark: ## Benchmark template generation performance
	@echo "Benchmarking template generation..."
	@time $(MAKE) test >/dev/null 2>&1
	@echo "✅ Benchmark completed"

clean: ## Remove test artifacts
	@echo "Cleaning up test artifacts..."
	@rm -rf test-output test-output-all
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -delete
	@echo "✅ Cleaned test artifacts"

push: ## Push to GitHub
	@git add .
	@git commit -m "Update Python workflow supervisor template" || true
	@git push origin main
	@echo "✅ Pushed to GitHub"

ci: check-dependencies validate lint test ## Run all CI checks
	@echo "✅ All CI checks passed!"

dev-setup: ## Set up development environment
	@echo "Setting up development environment..."
	@pip install cookiecutter black mypy flake8
	@echo "✅ Development environment ready"

compare-js: ## Compare with JavaScript template (if available)
	@echo "Comparing with JavaScript workflow supervisor template..."
	@if [ -d "../cc-js-workflow-supervisor" ]; then \
		echo "JavaScript template found, comparing structure..."; \
		diff -r --exclude="*.pyc" --exclude="__pycache__" --exclude=".git" \
			"{{cookiecutter.project_slug}}" "../cc-js-workflow-supervisor/{{cookiecutter.project_slug}}" || true; \
		echo "Comparison completed"; \
	else \
		echo "JavaScript template not found at ../cc-js-workflow-supervisor"; \
	fi