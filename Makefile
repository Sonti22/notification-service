.PHONY: help install test lint format clean run docker-up docker-down

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install dependencies
	pip install -r requirements.txt

test: ## Run tests with coverage
	pytest -v --cov=src --cov-report=term-missing --cov-report=html

test-unit: ## Run unit tests only
	pytest tests/unit/ -v

test-integration: ## Run integration tests only
	pytest tests/integration/ -v

lint: ## Run linters (ruff, mypy)
	ruff check src/ tests/
	mypy src/

format: ## Format code (black, ruff)
	black src/ tests/
	ruff check --fix src/ tests/

clean: ## Clean build artifacts
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	rm -rf .pytest_cache/ .mypy_cache/ .coverage htmlcov/ dist/ build/ *.egg-info

run: ## Run API locally (requires Redis)
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

run-worker: ## Run retry worker locally
	python -m src.services.retry

docker-up: ## Start all services with Docker Compose
	docker-compose up --build

docker-down: ## Stop all services
	docker-compose down -v

docker-logs: ## Tail logs
	docker-compose logs -f

