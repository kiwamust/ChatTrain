# ChatTrain MVP1 Makefile
# Convenient commands for development and deployment

.PHONY: help setup dev build test clean logs status health stop restart deploy backup restore

# Default target
.DEFAULT_GOAL := help

# Colors for output
CYAN := \033[36m
GREEN := \033[32m
YELLOW := \033[33m
RED := \033[31m
RESET := \033[0m

# Configuration
COMPOSE_FILE := docker-compose.yml
COMPOSE_PROD_FILE := docker-compose.prod.yml
BACKEND_DIR := src/backend
FRONTEND_DIR := src/frontend

help: ## Show this help message
	@echo "$(CYAN)ChatTrain MVP1 - Available Commands$(RESET)"
	@echo ""
	@echo "$(GREEN)Setup & Installation:$(RESET)"
	@awk 'BEGIN {FS = ":.*##"; category=""} /^## /{category=substr($$0,4)} /^[a-zA-Z_-]+:.*?##/ { if (category) {printf "  $(YELLOW)%s$(RESET)\n", category; category=""} printf "  $(CYAN)%-15s$(RESET) %s\n", $$1, $$2 }' $(MAKEFILE_LIST)

## Setup & Installation
setup: ## Setup development environment (run once)
	@echo "$(CYAN)Setting up ChatTrain development environment...$(RESET)"
	@chmod +x scripts/*.sh
	@./scripts/setup.sh
	@echo "$(GREEN)✅ Setup completed!$(RESET)"

install: setup ## Alias for setup

## Development
dev: ## Start development environment
	@echo "$(CYAN)Starting ChatTrain development environment...$(RESET)"
	@./scripts/start_dev.sh

dev-logs: ## Start development environment and follow logs
	@echo "$(CYAN)Starting ChatTrain development environment with logs...$(RESET)"
	@./scripts/start_dev.sh --logs

dev-build: ## Build and start development environment
	@echo "$(CYAN)Building and starting development environment...$(RESET)"
	@docker compose build
	@make dev

## Testing
test: ## Run all tests
	@echo "$(CYAN)Running ChatTrain tests...$(RESET)"
	@echo "Running backend tests..."
	@cd $(BACKEND_DIR) && python -m pytest tests/ -v
	@echo "Running frontend tests..."
	@cd $(FRONTEND_DIR) && npm test
	@echo "Running integration tests..."
	@python scripts/integration_test_enhanced.py
	@echo "$(GREEN)✅ All tests completed!$(RESET)"

test-backend: ## Run backend tests only
	@echo "$(CYAN)Running backend tests...$(RESET)"
	@cd $(BACKEND_DIR) && python -m pytest tests/ -v

test-frontend: ## Run frontend tests only
	@echo "$(CYAN)Running frontend tests...$(RESET)"
	@cd $(FRONTEND_DIR) && npm test

test-integration: ## Run integration tests
	@echo "$(CYAN)Running integration tests...$(RESET)"
	@python scripts/integration_test_enhanced.py

test-load: ## Run load tests
	@echo "$(CYAN)Running load tests...$(RESET)"
	@python scripts/load_test.py

## Production
build: ## Build production Docker images
	@echo "$(CYAN)Building production Docker images...$(RESET)"
	@docker build -f Dockerfile.backend -t chattrain-backend:latest .
	@docker build -f Dockerfile.frontend -t chattrain-frontend:latest .
	@echo "$(GREEN)✅ Production images built!$(RESET)"

deploy: ## Deploy to production
	@echo "$(CYAN)Deploying ChatTrain to production...$(RESET)"
	@./scripts/deploy_prod.sh
	@echo "$(GREEN)✅ Production deployment completed!$(RESET)"

deploy-backup: ## Deploy to production with backup
	@echo "$(CYAN)Deploying ChatTrain to production with backup...$(RESET)"
	@./scripts/deploy_prod.sh --backup
	@echo "$(GREEN)✅ Production deployment with backup completed!$(RESET)"

## Monitoring & Maintenance
status: ## Show service status
	@echo "$(CYAN)ChatTrain Service Status:$(RESET)"
	@docker compose ps

status-prod: ## Show production service status
	@echo "$(CYAN)ChatTrain Production Service Status:$(RESET)"
	@docker compose -f $(COMPOSE_PROD_FILE) ps

health: ## Run health checks (development)
	@echo "$(CYAN)Running health checks...$(RESET)"
	@./scripts/health_check.sh

health-prod: ## Run health checks (production)
	@echo "$(CYAN)Running production health checks...$(RESET)"
	@./scripts/health_check.sh --prod

logs: ## Show development logs
	@echo "$(CYAN)Showing development logs...$(RESET)"
	@docker compose logs -f

logs-prod: ## Show production logs
	@echo "$(CYAN)Showing production logs...$(RESET)"
	@docker compose -f $(COMPOSE_PROD_FILE) logs -f

logs-backend: ## Show backend logs only
	@docker compose logs -f backend

logs-frontend: ## Show frontend logs only
	@docker compose logs -f frontend

logs-db: ## Show database logs only
	@docker compose logs -f database

## Control
stop: ## Stop development services
	@echo "$(CYAN)Stopping ChatTrain development services...$(RESET)"
	@docker compose down
	@echo "$(GREEN)✅ Development services stopped$(RESET)"

stop-prod: ## Stop production services
	@echo "$(CYAN)Stopping ChatTrain production services...$(RESET)"
	@docker compose -f $(COMPOSE_PROD_FILE) down
	@echo "$(GREEN)✅ Production services stopped$(RESET)"

restart: ## Restart development services
	@echo "$(CYAN)Restarting ChatTrain development services...$(RESET)"
	@docker compose restart
	@echo "$(GREEN)✅ Development services restarted$(RESET)"

restart-prod: ## Restart production services
	@echo "$(CYAN)Restarting ChatTrain production services...$(RESET)"
	@docker compose -f $(COMPOSE_PROD_FILE) restart
	@echo "$(GREEN)✅ Production services restarted$(RESET)"

restart-backend: ## Restart backend service only
	@docker compose restart backend

restart-frontend: ## Restart frontend service only
	@docker compose restart frontend

## Data Management
backup: ## Create data backup
	@echo "$(CYAN)Creating ChatTrain data backup...$(RESET)"
	@mkdir -p backups/$(shell date +%Y%m%d_%H%M%S)
	@docker compose exec -T database pg_dump -U chattrain chattrain > backups/$(shell date +%Y%m%d_%H%M%S)/database.sql
	@docker run --rm -v chattrain_chattrain_data:/data -v $(PWD)/backups/$(shell date +%Y%m%d_%H%M%S):/backup alpine tar czf /backup/chattrain_data.tar.gz -C /data .
	@echo "$(GREEN)✅ Backup created in backups/$(shell date +%Y%m%d_%H%M%S)$(RESET)"

backup-prod: ## Create production data backup
	@echo "$(CYAN)Creating production data backup...$(RESET)"
	@mkdir -p backups/prod_$(shell date +%Y%m%d_%H%M%S)
	@docker compose -f $(COMPOSE_PROD_FILE) exec -T database pg_dump -U chattrain chattrain > backups/prod_$(shell date +%Y%m%d_%H%M%S)/database.sql
	@docker run --rm -v chattrain_chattrain_data:/data -v $(PWD)/backups/prod_$(shell date +%Y%m%d_%H%M%S):/backup alpine tar czf /backup/chattrain_data.tar.gz -C /data .
	@echo "$(GREEN)✅ Production backup created in backups/prod_$(shell date +%Y%m%d_%H%M%S)$(RESET)"

restore: ## Restore from backup (specify BACKUP_DIR)
	@if [ -z "$(BACKUP_DIR)" ]; then echo "$(RED)Please specify BACKUP_DIR: make restore BACKUP_DIR=backups/20231201_120000$(RESET)"; exit 1; fi
	@echo "$(CYAN)Restoring from backup: $(BACKUP_DIR)...$(RESET)"
	@docker compose exec -T database psql -U chattrain -d chattrain < $(BACKUP_DIR)/database.sql
	@docker run --rm -v chattrain_chattrain_data:/data -v $(PWD)/$(BACKUP_DIR):/backup alpine tar xzf /backup/chattrain_data.tar.gz -C /data
	@echo "$(GREEN)✅ Restore completed from $(BACKUP_DIR)$(RESET)"

reset-db: ## Reset database (WARNING: destroys all data)
	@echo "$(RED)WARNING: This will destroy all data!$(RESET)"
	@read -p "Are you sure? Type 'yes' to continue: " confirm && [ "$$confirm" = "yes" ]
	@docker compose down
	@docker volume rm chattrain_postgres_data || true
	@docker volume rm chattrain_chattrain_data || true
	@docker compose up -d database
	@sleep 10
	@docker compose up -d
	@echo "$(GREEN)✅ Database reset completed$(RESET)"

## Maintenance & Cleanup
clean: ## Clean up containers, images, and volumes
	@echo "$(CYAN)Cleaning up ChatTrain resources...$(RESET)"
	@docker compose down -v
	@docker system prune -f
	@echo "$(GREEN)✅ Cleanup completed$(RESET)"

clean-all: ## Clean up everything including images
	@echo "$(CYAN)Cleaning up all ChatTrain resources...$(RESET)"
	@docker compose down -v --rmi all
	@docker system prune -af
	@echo "$(GREEN)✅ Complete cleanup completed$(RESET)"

update: ## Update dependencies
	@echo "$(CYAN)Updating ChatTrain dependencies...$(RESET)"
	@cd $(BACKEND_DIR) && pip install --upgrade -r requirements.txt
	@cd $(FRONTEND_DIR) && npm update
	@echo "$(GREEN)✅ Dependencies updated$(RESET)"

## Quick Commands
quick-start: setup dev ## Quick start: setup and run development environment

quick-deploy: build deploy ## Quick deploy: build and deploy to production

quick-test: ## Quick test: run essential tests
	@echo "$(CYAN)Running quick tests...$(RESET)"
	@python scripts/integration_test.py
	@./scripts/health_check.sh
	@echo "$(GREEN)✅ Quick tests completed$(RESET)"

## Information
info: ## Show system information
	@echo "$(CYAN)ChatTrain System Information:$(RESET)"
	@echo "Docker version: $(shell docker --version)"
	@echo "Docker Compose version: $(shell docker compose version)"
	@echo "Node.js version: $(shell node --version)"
	@echo "Python version: $(shell python3 --version)"
	@echo "Project directory: $(PWD)"
	@echo "Backend directory: $(BACKEND_DIR)"
	@echo "Frontend directory: $(FRONTEND_DIR)"

urls: ## Show application URLs
	@echo "$(CYAN)ChatTrain Application URLs:$(RESET)"
	@echo "🌐 Frontend (Development): http://localhost:3000"
	@echo "🔗 Backend API (Development): http://localhost:8000"
	@echo "📊 API Documentation: http://localhost:8000/docs"
	@echo "🗄️ Database: localhost:5432 (chattrain/chattrain123)"
	@echo "🔴 Redis: localhost:6379"
	@echo ""
	@echo "$(YELLOW)Production URLs:$(RESET)"
	@echo "🌐 Frontend (Production): http://localhost:80"
	@echo "🔗 Backend API (Production): http://localhost:8000 (internal)"

## Help for specific topics
help-setup: ## Show setup help
	@echo "$(CYAN)ChatTrain Setup Help:$(RESET)"
	@echo ""
	@echo "1. First time setup:"
	@echo "   make setup"
	@echo ""
	@echo "2. Start development:"
	@echo "   make dev"
	@echo ""
	@echo "3. Run tests:"
	@echo "   make test"
	@echo ""
	@echo "4. Deploy to production:"
	@echo "   make deploy"

help-troubleshooting: ## Show troubleshooting help
	@echo "$(CYAN)ChatTrain Troubleshooting:$(RESET)"
	@echo ""
	@echo "Common issues and solutions:"
	@echo ""
	@echo "1. Services won't start:"
	@echo "   - Check Docker is running: docker info"
	@echo "   - Check logs: make logs"
	@echo "   - Reset: make clean && make dev"
	@echo ""
	@echo "2. Database connection issues:"
	@echo "   - Check DB status: make logs-db"
	@echo "   - Reset DB: make reset-db"
	@echo ""
	@echo "3. Health check failures:"
	@echo "   - Run health check: make health"
	@echo "   - Check individual services: make status"
	@echo ""
	@echo "4. For more help, see README.md or docs/"