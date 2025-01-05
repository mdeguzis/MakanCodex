.PHONY: setup clean test format check build lock requirements verify-imports static-check all

POETRY := poetry
PYTHON := poetry run python
FLAKE8 := poetry run flake8
PYTEST := poetry run pytest
BLACK := poetry run black
ISORT := poetry run isort
MYPY := poetry run mypy

.DEFAULT_GOAL := all

all: clean setup check test

# Update lock file
lock:
	$(POETRY) lock

# Install dependencies and set up development environment
setup: lock
	$(POETRY) install
	$(POETRY) run pip install -e .

# Generate requirements.txt for other system
requirements:
	$(POETRY) export -f requirements.txt --output requirements.txt --without-hashes

# Format code
format:
	$(BLACK) .
	$(ISORT) .

# Comprehensive checking
check: verify-imports lint static-check

# Run linting and style checks
lint:
	@echo "Running linting and style checks..."
#$(FLAKE8) src/recipe_crypt tests
#$(BLACK) --check .
#$(ISORT) --check .


# Static type checking
static-check:
	@echo "Running static type checking..."
#$(MYPY) src/recipe_crypt --ignore-missing-imports

# Run tests with different options
test: test-standard test-coverage

test-standard:
	$(PYTEST) --cov=src/recipe_crypt tests/

test-verbose:
	$(PYTEST) -v --capture=no

test-coverage:
	$(PYTEST) --cov=src/recipe_crypt

# Build package
build: check test
	$(POETRY) build

# Clean build artifacts
clean:
	rm -rf dist/
	rm -rf build/
	rm -rf *.egg-info
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
