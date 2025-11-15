.PHONY: help install test lint format type-check security docs clean build all check pre-commit

# Variables
PYTHON := poetry run python
PYTEST := poetry run pytest
RUFF := poetry run ruff
MYPY := poetry run mypy
BANDIT := poetry run bandit
SAFETY := poetry run safety
INTERROGATE := poetry run interrogate
VULTURE := poetry run vulture
BLACK := poetry run black
ISORT := poetry run isort

# Directories
SRC_DIR := src
TEST_DIR := tests
DOCS_DIR := docs
DIST_DIR := dist
HTMLCOV_DIR := htmlcov

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
RED := \033[0;31m
NC := \033[0m # No Color

##@ Help

help: ## Display this help message
	@echo "$(BLUE)Devorbit Multi-LLM SDK - Development Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(YELLOW)<target>$(NC)\n"} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Setup

install: ## Install project dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	poetry install --with dev
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-pre-commit: install ## Install pre-commit hooks
	@echo "$(BLUE)Installing pre-commit hooks...$(NC)"
	$(PYTHON) -m pre_commit install
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

##@ Testing

test: ## Run all tests with coverage
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	$(PYTEST)
	@echo "$(GREEN)✓ Tests completed$(NC)"

test-fast: ## Run tests without coverage (faster)
	@echo "$(BLUE)Running tests (no coverage)...$(NC)"
	$(PYTEST) --no-cov
	@echo "$(GREEN)✓ Tests completed$(NC)"

test-parallel: ## Run tests in parallel
	@echo "$(BLUE)Running tests in parallel...$(NC)"
	$(PYTEST) -n auto
	@echo "$(GREEN)✓ Tests completed$(NC)"

test-verbose: ## Run tests with verbose output
	@echo "$(BLUE)Running tests (verbose)...$(NC)"
	$(PYTEST) -vv
	@echo "$(GREEN)✓ Tests completed$(NC)"

test-specific: ## Run specific test file (usage: make test-specific FILE=test_web_tools.py)
	@echo "$(BLUE)Running specific test: $(FILE)...$(NC)"
	$(PYTEST) $(TEST_DIR)/$(FILE)
	@echo "$(GREEN)✓ Test completed$(NC)"

test-coverage: test ## Generate coverage report (alias for test)
	@echo "$(GREEN)✓ Coverage report generated in $(HTMLCOV_DIR)/$(NC)"

##@ Code Quality

lint: ## Run ruff linter
	@echo "$(BLUE)Running ruff linter...$(NC)"
	$(RUFF) check $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)✓ Linting completed$(NC)"

lint-fix: ## Run ruff linter with auto-fix
	@echo "$(BLUE)Running ruff linter with auto-fix...$(NC)"
	$(RUFF) check --fix $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)✓ Linting completed with fixes$(NC)"

format: ## Format code with ruff
	@echo "$(BLUE)Formatting code with ruff...$(NC)"
	$(RUFF) format $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)✓ Code formatted$(NC)"

format-check: ## Check code formatting without changes
	@echo "$(BLUE)Checking code formatting...$(NC)"
	$(RUFF) format --check $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)✓ Format check completed$(NC)"

isort: ## Sort imports with isort
	@echo "$(BLUE)Sorting imports...$(NC)"
	$(ISORT) $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)✓ Imports sorted$(NC)"

isort-check: ## Check import sorting
	@echo "$(BLUE)Checking import sorting...$(NC)"
	$(ISORT) --check-only $(SRC_DIR) $(TEST_DIR)
	@echo "$(GREEN)✓ Import check completed$(NC)"

type-check: ## Run mypy type checker
	@echo "$(BLUE)Running mypy type checker...$(NC)"
	$(MYPY) $(SRC_DIR)
	@echo "$(GREEN)✓ Type checking completed$(NC)"

##@ Security

security: ## Run all security checks
	@echo "$(BLUE)Running security checks...$(NC)"
	@$(MAKE) security-bandit
	@$(MAKE) security-safety
	@echo "$(GREEN)✓ All security checks completed$(NC)"

security-bandit: ## Run bandit security scanner
	@echo "$(BLUE)Running bandit security scanner...$(NC)"
	$(BANDIT) -r $(SRC_DIR) -c pyproject.toml
	@echo "$(GREEN)✓ Bandit scan completed$(NC)"

security-safety: ## Check dependencies for known vulnerabilities
	@echo "$(BLUE)Checking dependencies for vulnerabilities...$(NC)"
	$(SAFETY) check --json || echo "$(YELLOW)⚠ Some vulnerabilities found$(NC)"
	@echo "$(GREEN)✓ Safety check completed$(NC)"

##@ Documentation

docs-coverage: ## Check documentation coverage
	@echo "$(BLUE)Checking documentation coverage...$(NC)"
	$(INTERROGATE) $(SRC_DIR)
	@echo "$(GREEN)✓ Documentation coverage check completed$(NC)"

dead-code: ## Find dead/unused code
	@echo "$(BLUE)Finding dead code...$(NC)"
	$(VULTURE) $(SRC_DIR) --min-confidence 80
	@echo "$(GREEN)✓ Dead code check completed$(NC)"

##@ Building

build: clean ## Build distribution packages
	@echo "$(BLUE)Building distribution packages...$(NC)"
	poetry build
	@echo "$(GREEN)✓ Build completed$(NC)"

publish: build ## Build and publish to PyPI (requires authentication)
	@echo "$(BLUE)Publishing to PyPI...$(NC)"
	poetry publish
	@echo "$(GREEN)✓ Published to PyPI$(NC)"

publish-test: build ## Publish to TestPyPI
	@echo "$(BLUE)Publishing to TestPyPI...$(NC)"
	poetry publish -r testpypi
	@echo "$(GREEN)✓ Published to TestPyPI$(NC)"

##@ Cleaning

clean: ## Remove build artifacts and cache files
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf $(DIST_DIR) $(HTMLCOV_DIR) .coverage coverage.xml
	rm -rf .pytest_cache .mypy_cache .ruff_cache
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleanup completed$(NC)"

clean-all: clean ## Remove all generated files including venv
	@echo "$(BLUE)Removing virtual environment...$(NC)"
	poetry env remove --all || true
	@echo "$(GREEN)✓ Full cleanup completed$(NC)"

##@ Pre-commit

pre-commit: ## Run all pre-commit checks manually
	@echo "$(BLUE)Running pre-commit checks...$(NC)"
	$(PYTHON) -m pre_commit run --all-files
	@echo "$(GREEN)✓ Pre-commit checks completed$(NC)"

##@ CI/CD

check: ## Run all checks (linting, formatting, type-check)
	@echo "$(BLUE)Running all code quality checks...$(NC)"
	@$(MAKE) format-check
	@$(MAKE) lint
	@$(MAKE) type-check
	@echo "$(GREEN)✓ All checks passed$(NC)"

ci: ## Run full CI pipeline (what runs in CI/CD)
	@echo "$(BLUE)================================$(NC)"
	@echo "$(BLUE)Running Full CI Pipeline...$(NC)"
	@echo "$(BLUE)================================$(NC)"
	@echo ""
	@$(MAKE) check
	@echo ""
	@$(MAKE) test
	@echo ""
	@$(MAKE) security
	@echo ""
	@$(MAKE) docs-coverage
	@echo ""
	@echo "$(GREEN)================================$(NC)"
	@echo "$(GREEN)✓ CI Pipeline Completed Successfully!$(NC)"
	@echo "$(GREEN)================================$(NC)"

all: clean install ci build ## Run everything: clean, install, CI checks, and build
	@echo ""
	@echo "$(GREEN)================================$(NC)"
	@echo "$(GREEN)✓ All Tasks Completed!$(NC)"
	@echo "$(GREEN)================================$(NC)"

quick-check: format-check lint ## Quick checks before committing (fast)
	@echo "$(GREEN)✓ Quick checks passed$(NC)"

##@ Development

dev: install install-pre-commit ## Setup development environment
	@echo "$(GREEN)✓ Development environment ready!$(NC)"

watch-test: ## Watch for changes and run tests automatically
	@echo "$(BLUE)Watching for changes...$(NC)"
	$(PYTEST) --looponfail

shell: ## Open poetry shell
	poetry shell

update: ## Update dependencies
	@echo "$(BLUE)Updating dependencies...$(NC)"
	poetry update
	@echo "$(GREEN)✓ Dependencies updated$(NC)"

show-deps: ## Show dependency tree
	poetry show --tree

##@ Information

info: ## Show project information
	@echo "$(BLUE)Project Information:$(NC)"
	@echo "  Name: devorbit-multi-llm-sdk"
	@echo "  Version: 0.1.0"
	@echo "  Python: 3.12+"
	@echo ""
	@echo "$(BLUE)Available Tools:$(NC)"
	@echo "  - pytest: Testing framework"
	@echo "  - ruff: Linting and formatting"
	@echo "  - mypy: Type checking"
	@echo "  - bandit: Security scanning"
	@echo "  - safety: Dependency vulnerability checking"
	@echo "  - interrogate: Documentation coverage"
	@echo "  - vulture: Dead code detection"

version: ## Show installed versions
	@echo "$(BLUE)Installed Versions:$(NC)"
	@poetry --version
	@$(PYTHON) --version
	@$(PYTEST) --version
	@$(RUFF) --version
	@$(MYPY) --version
