# Intelligent Data Quality Platform - Makefile

.PHONY: help setup dev-up dev-down test clean logs

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Initial setup
	@echo "🚀 Setting up Intelligent Data Quality Platform..."
	chmod +x scripts/setup.sh
	./scripts/setup.sh

dev-up: ## Start development environment
	@echo "🔥 Starting development environment..."
	docker-compose up -d
	@echo "✅ Services started!"
	@echo "🌐 Frontend: http://localhost:3000"
	@echo "🔧 Backend API: http://localhost:8000"
	@echo "📊 Grafana: http://localhost:3001 (admin/admin)"
	@echo "⚡ Spark UI: http://localhost:8080"

dev-down: ## Stop development environment
	@echo "🛑 Stopping development environment..."
	docker-compose down

dev-restart: ## Restart development environment
	@echo "🔄 Restarting development environment..."
	docker-compose restart

logs: ## Show logs for all services
	docker-compose logs -f

logs-backend: ## Show backend logs
	docker-compose logs -f backend

logs-frontend: ## Show frontend logs
	docker-compose logs -f frontend

test: ## Run tests
	@echo "🧪 Running tests..."
	cd backend && python -m pytest
	cd frontend && npm test

test-backend: ## Run backend tests
	cd backend && python -m pytest

test-frontend: ## Run frontend tests
	cd frontend && npm test

lint: ## Run linting
	cd backend && python -m flake8 app/
	cd frontend && npm run lint

build: ## Build all services
	docker-compose build

clean: ## Clean up containers and volumes
	@echo "🧹 Cleaning up..."
	docker-compose down -v
	docker system prune -f

status: ## Show service status
	docker-compose ps

shell-backend: ## Open shell in backend container
	docker-compose exec backend bash

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend sh

db-shell: ## Open PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d data_quality

redis-shell: ## Open Redis shell
	docker-compose exec redis redis-cli

generate-data: ## Generate sample data
	python scripts/data_generator.py

benchmark: ## Run performance benchmarks
	python scripts/performance_benchmark.py

deploy-prod: ## Deploy to production
	@echo "🚀 Deploying to production..."
	docker-compose -f docker-compose.prod.yml up -d
