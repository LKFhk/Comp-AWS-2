# RiskIntel360 Platform Deployment Makefile

.PHONY: help build test deploy clean

# Default environment
ENV ?= development
REGION ?= us-east-1
IMAGE_TAG ?= latest

# Colors for output
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)RiskIntel360 Platform Deployment Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(GREEN)%-20s$(NC) %s\n", $$1, $$2}'

# Development Commands
dev-setup: ## Set up development environment
	@echo "$(YELLOW)Setting up development environment...$(NC)"
	@docker-compose --profile dev up -d postgres redis
	@echo "$(GREEN)Development environment ready!$(NC)"

dev-start: ## Start development server
	@echo "$(YELLOW)Starting development server...$(NC)"
	@docker-compose --profile dev up riskintel360-dev

dev-stop: ## Stop development environment
	@echo "$(YELLOW)Stopping development environment...$(NC)"
	@docker-compose --profile dev down

dev-logs: ## Show development logs
	@docker-compose --profile dev logs -f riskintel360-dev

dev-shell: ## Open shell in development container
	@docker-compose --profile dev exec riskintel360-dev /bin/bash

# Testing Commands
test: ## Run all tests
	@echo "$(YELLOW)Running tests...$(NC)"
	@docker-compose --profile dev exec riskintel360-dev pytest tests/ -v

test-unit: ## Run unit tests only
	@echo "$(YELLOW)Running unit tests...$(NC)"
	@docker-compose --profile dev exec riskintel360-dev pytest tests/ -v -m "not integration"

test-integration: ## Run integration tests only
	@echo "$(YELLOW)Running integration tests...$(NC)"
	@docker-compose --profile dev exec riskintel360-dev pytest tests/ -v -m integration

test-coverage: ## Run tests with coverage
	@echo "$(YELLOW)Running tests with coverage...$(NC)"
	@docker-compose --profile dev exec riskintel360-dev pytest tests/ --cov=riskintel360 --cov-report=html

# Code Quality Commands
lint: ## Run linting
	@echo "$(YELLOW)Running linting...$(NC)"
	@docker-compose --profile dev exec riskintel360-dev flake8 riskintel360/ tests/

format: ## Format code
	@echo "$(YELLOW)Formatting code...$(NC)"
	@docker-compose --profile dev exec riskintel360-dev black riskintel360/ tests/

type-check: ## Run type checking
	@echo "$(YELLOW)Running type checking...$(NC)"
	@docker-compose --profile dev exec riskintel360-dev mypy riskintel360/

quality: lint format type-check ## Run all code quality checks

# Build Commands
build: ## Build Docker image
	@echo "$(YELLOW)Building Docker image...$(NC)"
	@docker build -t riskintel360-platform:$(IMAGE_TAG) .
	@echo "$(GREEN)Docker image built successfully!$(NC)"

build-dev: ## Build development Docker image
	@echo "$(YELLOW)Building development Docker image...$(NC)"
	@docker build --target development -t riskintel360-platform:dev .
	@echo "$(GREEN)Development Docker image built successfully!$(NC)"

build-prod: ## Build production Docker image
	@echo "$(YELLOW)Building production Docker image...$(NC)"
	@docker build --target production -t riskintel360-platform:prod .
	@echo "$(GREEN)Production Docker image built successfully!$(NC)"

# Infrastructure Commands
infra-bootstrap: ## Bootstrap CDK infrastructure
	@echo "$(YELLOW)Bootstrapping CDK infrastructure...$(NC)"
	@cd infrastructure && cdk bootstrap --context environment=$(ENV)

infra-synth: ## Synthesize CDK infrastructure
	@echo "$(YELLOW)Synthesizing CDK infrastructure...$(NC)"
	@cd infrastructure && cdk synth --context environment=$(ENV)

infra-diff: ## Show infrastructure differences
	@echo "$(YELLOW)Showing infrastructure differences...$(NC)"
	@cd infrastructure && cdk diff --context environment=$(ENV)

infra-deploy: ## Deploy infrastructure
	@echo "$(YELLOW)Deploying infrastructure for $(ENV)...$(NC)"
	@cd infrastructure && cdk deploy --context environment=$(ENV) --require-approval never
	@echo "$(GREEN)Infrastructure deployed successfully!$(NC)"

infra-destroy: ## Destroy infrastructure
	@echo "$(RED)Destroying infrastructure for $(ENV)...$(NC)"
	@read -p "Are you sure you want to destroy $(ENV) infrastructure? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		cd infrastructure && cdk destroy --context environment=$(ENV) --force; \
	fi

# Deployment Commands
deploy-dev: ## Deploy to development environment
	@echo "$(YELLOW)Deploying to development environment...$(NC)"
	@python scripts/deploy.py --environment development --image-tag $(IMAGE_TAG) --strategy rolling
	@echo "$(GREEN)Development deployment completed!$(NC)"

deploy-staging: ## Deploy to staging environment
	@echo "$(YELLOW)Deploying to staging environment...$(NC)"
	@python scripts/deploy.py --environment staging --image-tag $(IMAGE_TAG) --strategy blue-green
	@echo "$(GREEN)Staging deployment completed!$(NC)"

deploy-prod: ## Deploy to production environment
	@echo "$(YELLOW)Deploying to production environment...$(NC)"
	@python scripts/deploy.py --environment production --image-tag $(IMAGE_TAG) --strategy blue-green
	@echo "$(GREEN)Production deployment completed!$(NC)"

# Validation Commands
validate-dev: ## Validate development deployment
	@echo "$(YELLOW)Validating development deployment...$(NC)"
	@python scripts/validate-deployment.py --environment development

validate-staging: ## Validate staging deployment
	@echo "$(YELLOW)Validating staging deployment...$(NC)"
	@python scripts/validate-deployment.py --environment staging

validate-prod: ## Validate production deployment
	@echo "$(YELLOW)Validating production deployment...$(NC)"
	@python scripts/validate-deployment.py --environment production

# Smoke Tests
smoke-dev: ## Run smoke tests on development
	@echo "$(YELLOW)Running smoke tests on development...$(NC)"
	@python scripts/smoke-tests.py --environment development

smoke-staging: ## Run smoke tests on staging
	@echo "$(YELLOW)Running smoke tests on staging...$(NC)"
	@python scripts/smoke-tests.py --environment staging

smoke-prod: ## Run smoke tests on production
	@echo "$(YELLOW)Running smoke tests on production...$(NC)"
	@python scripts/smoke-tests.py --environment production

# Integration Tests
integration-staging: ## Run integration tests on staging
	@echo "$(YELLOW)Running integration tests on staging...$(NC)"
	@python scripts/integration-tests.py --environment staging

integration-prod: ## Run integration tests on production
	@echo "$(YELLOW)Running integration tests on production...$(NC)"
	@python scripts/integration-tests.py --environment production

# Rollback Commands
rollback-staging: ## Rollback staging deployment
	@echo "$(YELLOW)Rolling back staging deployment...$(NC)"
	@python scripts/rollback.py --environment staging

rollback-prod: ## Rollback production deployment
	@echo "$(RED)Rolling back production deployment...$(NC)"
	@read -p "Are you sure you want to rollback production? [y/N] " -n 1 -r; \
	echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		python scripts/rollback.py --environment production; \
	fi

rollback-list: ## List deployment history
	@echo "$(YELLOW)Listing deployment history for $(ENV)...$(NC)"
	@python scripts/rollback.py --environment $(ENV) --list-history

# Environment Management
env-up: ## Start environment-specific services
	@echo "$(YELLOW)Starting $(ENV) environment...$(NC)"
	@if [ "$(ENV)" = "development" ]; then \
		docker-compose --profile dev up -d; \
	elif [ "$(ENV)" = "staging" ]; then \
		docker-compose -f docker-compose.yml -f docker-compose.staging.yml up -d; \
	elif [ "$(ENV)" = "production" ]; then \
		docker-compose -f docker-compose.yml -f docker-compose.production.yml up -d; \
	fi

env-down: ## Stop environment-specific services
	@echo "$(YELLOW)Stopping $(ENV) environment...$(NC)"
	@if [ "$(ENV)" = "development" ]; then \
		docker-compose --profile dev down; \
	elif [ "$(ENV)" = "staging" ]; then \
		docker-compose -f docker-compose.yml -f docker-compose.staging.yml down; \
	elif [ "$(ENV)" = "production" ]; then \
		docker-compose -f docker-compose.yml -f docker-compose.production.yml down; \
	fi

env-logs: ## Show environment-specific logs
	@if [ "$(ENV)" = "development" ]; then \
		docker-compose --profile dev logs -f; \
	elif [ "$(ENV)" = "staging" ]; then \
		docker-compose -f docker-compose.yml -f docker-compose.staging.yml logs -f; \
	elif [ "$(ENV)" = "production" ]; then \
		docker-compose -f docker-compose.yml -f docker-compose.production.yml logs -f; \
	fi

# Database Commands
db-migrate: ## Run database migrations
	@echo "$(YELLOW)Running database migrations...$(NC)"
	@docker-compose --profile dev exec riskintel360-dev alembic upgrade head

db-seed: ## Seed database with test data
	@echo "$(YELLOW)Seeding database with test data...$(NC)"
	@docker-compose --profile dev exec postgres psql -U riskintel360_user -d riskintel360 -f /docker-entrypoint-initdb.d/02-seed-data.sql

db-backup: ## Backup database
	@echo "$(YELLOW)Backing up database...$(NC)"
	@docker-compose --profile dev exec postgres pg_dump -U riskintel360_user riskintel360 > backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore: ## Restore database from backup
	@echo "$(YELLOW)Restoring database from backup...$(NC)"
	@read -p "Enter backup file path: " backup_file; \
	docker-compose --profile dev exec -T postgres psql -U riskintel360_user riskintel360 < $$backup_file

# Monitoring Commands
logs: ## Show application logs
	@docker-compose logs -f riskintel360-dev

logs-tail: ## Tail application logs
	@docker-compose logs --tail=100 -f riskintel360-dev

monitor: ## Start monitoring stack
	@echo "$(YELLOW)Starting monitoring stack...$(NC)"
	@docker-compose --profile monitoring up -d

# Security Commands
security-scan: ## Run security scan
	@echo "$(YELLOW)Running security scan...$(NC)"
	@docker run --rm -v $(PWD):/app -w /app securecodewarrior/docker-security-scanner

vulnerability-check: ## Check for vulnerabilities
	@echo "$(YELLOW)Checking for vulnerabilities...$(NC)"
	@docker-compose --profile dev exec riskintel360-dev pip-audit

# Cleanup Commands
clean: ## Clean up Docker resources
	@echo "$(YELLOW)Cleaning up Docker resources...$(NC)"
	@docker system prune -f
	@docker volume prune -f

clean-all: ## Clean up all Docker resources (including images)
	@echo "$(RED)Cleaning up all Docker resources...$(NC)"
	@docker system prune -af
	@docker volume prune -f

# Full Deployment Workflows
full-deploy-staging: build-prod infra-deploy deploy-staging validate-staging smoke-staging ## Full staging deployment
	@echo "$(GREEN)Full staging deployment completed successfully!$(NC)"

full-deploy-prod: build-prod infra-deploy deploy-prod validate-prod smoke-prod ## Full production deployment
	@echo "$(GREEN)Full production deployment completed successfully!$(NC)"

# CI/CD Simulation
ci-pipeline: quality test build ## Simulate CI pipeline
	@echo "$(GREEN)CI pipeline completed successfully!$(NC)"

cd-pipeline-staging: ci-pipeline deploy-staging validate-staging ## Simulate CD pipeline for staging
	@echo "$(GREEN)CD pipeline for staging completed successfully!$(NC)"

cd-pipeline-prod: ci-pipeline deploy-prod validate-prod ## Simulate CD pipeline for production
	@echo "$(GREEN)CD pipeline for production completed successfully!$(NC)"

# Status Commands
status: ## Show deployment status
	@echo "$(BLUE)riskintel360 Platform Status$(NC)"
	@echo "Environment: $(ENV)"
	@echo "Region: $(REGION)"
	@echo "Image Tag: $(IMAGE_TAG)"
	@echo ""
	@docker-compose ps

health-check: ## Run health checks
	@echo "$(YELLOW)Running health checks...$(NC)"
	@curl -f http://localhost:8000/health || echo "$(RED)Health check failed$(NC)"
