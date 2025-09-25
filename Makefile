.PHONY: help dev build test lint format clean install

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

dev: ## Start development environment
	docker-compose up -d postgres redis
	cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install
	@echo "Backend: http://localhost:8000"
	@echo "Frontend: http://localhost:3000"

build: ## Build all services
	docker-compose build

test: ## Run all tests
	cd backend && python -m pytest
	cd frontend && npm test

lint: ## Run linters
	cd backend && black --check . && flake8 . && mypy .
	cd frontend && npm run lint

format: ## Format code
	cd backend && black . && isort .
	cd frontend && npm run format

clean: ## Clean up
	docker-compose down -v
	rm -rf backend/venv
	rm -rf frontend/node_modules
	rm -rf frontend/.next

install: ## Install dependencies
	cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt
	cd frontend && npm install

migrate: ## Run database migrations
	cd backend && source venv/bin/activate && alembic upgrade head

seed: ## Seed database with sample data
	cd backend && source venv/bin/activate && python scripts/seed.py
