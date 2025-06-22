# ChatTrain MVP1 Deployment and Infrastructure Setup Guide

## Overview

This guide provides comprehensive instructions for setting up ChatTrain MVP1 in both development and production environments. The deployment strategy emphasizes local Mac development with GitHub-based CI/CD and containerized services.

## Prerequisites

### Development Environment
- **macOS**: 12.0 or later
- **Docker Desktop**: 4.20+ with Docker Compose V2
- **Node.js**: 20.0+ (recommend using nvm)
- **Python**: 3.11+ (recommend using pyenv)
- **Git**: 2.30+

### Production Environment
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **PostgreSQL**: 16+ (if not using Docker)
- **Reverse Proxy**: nginx or Traefik (recommended)

## Project Structure

```
chattrain/
├── src/
│   ├── frontend/          # React + Vite application
│   └── backend/           # FastAPI application
├── content/               # Training scenarios and materials
├── docs/                  # Documentation
├── scripts/               # Setup and utility scripts
├── tests/                 # Test suites
├── .github/workflows/     # CI/CD pipelines
├── docker/                # Docker configurations
├── docker-compose.yml     # Development services
├── docker-compose.prod.yml # Production services
├── Makefile              # Common commands
├── .env.example          # Environment template
└── README.md
```

## Development Setup

### 1. Initial Setup

```bash
# Clone repository
git clone https://github.com/your-org/chattrain.git
cd chattrain

# Copy environment template
cp .env.example .env

# Edit environment variables
vim .env
```

### 2. Environment Configuration

Create `.env` file with the following variables:

```bash
# Environment
NODE_ENV=development
ENVIRONMENT=development

# API Configuration
API_HOST=localhost
API_PORT=8000
FRONTEND_PORT=3000

# Database
DATABASE_URL=postgresql://chattrain:chattrain@localhost:5432/chattrain_dev
POSTGRES_USER=chattrain
POSTGRES_PASSWORD=chattrain
POSTGRES_DB=chattrain_dev

# Vector Database
PGVECTOR_URL=postgresql://chattrain:chattrain@localhost:5432/chattrain_dev

# LLM Configuration
OPENAI_API_KEY=your_openai_api_key_here
AZURE_OPENAI_ENDPOINT=your_azure_endpoint_here
AZURE_OPENAI_API_KEY=your_azure_key_here
LLM_PROVIDER=openai  # or azure

# Redis (optional, for Celery)
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your_secret_key_here
JWT_SECRET=your_jwt_secret_here

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
LLM_RATE_LIMIT_RPM=10

# File Upload
MAX_UPLOAD_SIZE_MB=10
UPLOAD_PATH=./uploads

# Session Configuration
SESSION_TIMEOUT_MINUTES=60
CLEANUP_INTERVAL_HOURS=24
```

### 3. Makefile Commands

```makefile
# Makefile
.PHONY: help setup dev test clean

help:		## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup:		## Initial project setup
	@echo "Setting up ChatTrain development environment..."
	./scripts/setup.sh

dev:		## Start development environment
	docker-compose up -d
	@echo "Starting frontend dev server..."
	cd src/frontend && npm run dev &
	@echo "Development environment ready at http://localhost:3000"

test:		## Run all tests
	@echo "Running backend tests..."
	cd src/backend && python -m pytest tests/
	@echo "Running frontend tests..."
	cd src/frontend && npm run test

build:		## Build production images
	docker-compose -f docker-compose.prod.yml build

deploy:		## Deploy to production
	docker-compose -f docker-compose.prod.yml up -d

clean:		## Clean development environment
	docker-compose down -v
	docker system prune -f
```

### 4. Setup Script

```bash
#!/bin/bash
# scripts/setup.sh

set -e

echo "🚀 Setting up ChatTrain development environment..."

# Check prerequisites
echo "📋 Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required but not installed. Aborting." >&2; exit 1; }
command -v node >/dev/null 2>&1 || { echo "❌ Node.js is required but not installed. Aborting." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python 3 is required but not installed. Aborting." >&2; exit 1; }

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please edit .env file with your configuration"
fi

# Backend setup
echo "🐍 Setting up Python backend..."
cd src/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Frontend setup
echo "📦 Setting up Node.js frontend..."
cd ../frontend
npm install

# Go back to root
cd ../..

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d postgres redis

# Wait for PostgreSQL to be ready
echo "⏳ Waiting for PostgreSQL to be ready..."
timeout 60s bash -c 'until docker-compose exec postgres pg_isready; do sleep 1; done'

# Run database migrations
echo "🗄️  Running database migrations..."
cd src/backend
source venv/bin/activate
alembic upgrade head

# Create sample scenarios
echo "📚 Creating sample scenarios..."
python scripts/create_sample_scenarios.py

# Install pre-commit hooks
echo "🔧 Installing pre-commit hooks..."
cd ../..
pip install pre-commit
pre-commit install

echo "✅ Setup complete! Run 'make dev' to start development environment."
```

## Docker Configuration

### Development Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-chattrain}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-chattrain}
      POSTGRES_DB: ${POSTGRES_DB:-chattrain_dev}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-chattrain}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

  backend:
    build:
      context: ./src/backend
      dockerfile: Dockerfile.dev
    ports:
      - "${API_PORT:-8000}:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./src/backend:/app
      - ./content:/app/content
      - backend_uploads:/app/uploads
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy
    develop:
      watch:
        - action: sync
          path: ./src/backend
          target: /app
        - action: rebuild
          path: ./src/backend/requirements.txt

volumes:
  postgres_data:
  redis_data:
  backend_uploads:
```

### Production Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./docker/nginx/ssl:/etc/nginx/ssl
      - static_files:/var/www/static
    depends_on:
      - frontend
      - backend
    restart: unless-stopped

  frontend:
    build:
      context: ./src/frontend
      dockerfile: Dockerfile.prod
    volumes:
      - static_files:/app/dist
    restart: unless-stopped

  backend:
    build:
      context: ./src/backend
      dockerfile: Dockerfile.prod
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ENVIRONMENT=production
    volumes:
      - ./content:/app/content:ro
      - backend_uploads:/app/uploads
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  celery-worker:
    build:
      context: ./src/backend
      dockerfile: Dockerfile.prod
    command: celery -A app.worker worker --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./content:/app/content:ro
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  celery-beat:
    build:
      context: ./src/backend
      dockerfile: Dockerfile.prod
    command: celery -A app.worker beat --loglevel=info
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    depends_on:
      - postgres
      - redis
    restart: unless-stopped

  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 3

volumes:
  postgres_data:
  redis_data:
  backend_uploads:
  static_files:
```

## Dockerfile Configurations

### Backend Development Dockerfile

```dockerfile
# src/backend/Dockerfile.dev
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8000

# Development command with auto-reload
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Backend Production Dockerfile

```dockerfile
# src/backend/Dockerfile.prod
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.11-slim

WORKDIR /app

# Copy Python dependencies from builder stage
COPY --from=builder /root/.local /root/.local

# Add local bin to PATH
ENV PATH=/root/.local/bin:$PATH

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app
RUN chown -R app:app /app
USER app

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Production command
CMD ["gunicorn", "app.main:app", "-w", "4", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]
```

### Frontend Production Dockerfile

```dockerfile
# src/frontend/Dockerfile.prod
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

FROM nginx:alpine

# Copy built application
COPY --from=builder /app/dist /var/www/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

## Nginx Configuration

```nginx
# docker/nginx/nginx.conf
upstream backend {
    server backend:8000;
}

server {
    listen 80;
    server_name localhost;

    # Frontend
    location / {
        root /var/www/html;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    # API
    location /api/ {
        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket
    location /chat/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Static files
    location /static/ {
        alias /var/www/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```

## CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      redis:
        image: redis:7
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.11'

    - name: Set up Node.js
      uses: actions/setup-node@v4
      with:
        node-version: '20'

    - name: Install backend dependencies
      run: |
        cd src/backend
        pip install -r requirements.txt
        pip install -r requirements-test.txt

    - name: Install frontend dependencies
      run: |
        cd src/frontend
        npm ci

    - name: Run backend tests
      run: |
        cd src/backend
        pytest --cov=app --cov-report=xml
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test
        REDIS_URL: redis://localhost:6379/0

    - name: Run frontend tests
      run: |
        cd src/frontend
        npm run test:coverage

    - name: Validate YAML scenarios
      run: |
        yamllint content/**/*.yaml
        python scripts/validate_scenarios.py

    - name: Upload coverage reports
      uses: codecov/codecov-action@v3

  build:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
    - name: Checkout code
      uses: actions/checkout@v4

    - name: Log in to Container Registry
      uses: docker/login-action@v3
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}

    - name: Build and push Docker images
      run: |
        docker-compose -f docker-compose.prod.yml build
        docker-compose -f docker-compose.prod.yml push

  deploy:
    needs: build
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    environment: production

    steps:
    - name: Deploy to production
      run: |
        # Add deployment script here
        echo "Deploying to production..."
```

## Database Migrations

### Alembic Configuration

```python
# src/backend/alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
from app.models.database import Base
from app.core.config import settings

config = context.config
fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_online():
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.DATABASE_URL
    
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()
```

### Migration Commands

```bash
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check current version
alembic current

# Show migration history
alembic history
```

## Monitoring and Logging

### Application Logging Configuration

```python
# src/backend/app/core/logging.py
import logging
import sys
from typing import Dict, Any
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_entry: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        
        # Add custom fields
        if hasattr(record, 'user_id'):
            log_entry["user_id"] = record.user_id
        if hasattr(record, 'session_id'):
            log_entry["session_id"] = record.session_id
        if hasattr(record, 'request_id'):
            log_entry["request_id"] = record.request_id
            
        return json.dumps(log_entry)

def setup_logging():
    """Configure application logging"""
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # Remove default handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    root_logger.addHandler(console_handler)
    
    # Set specific log levels
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
```

### Health Check Endpoint

```python
# src/backend/app/api/health.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.llm import LLMService

router = APIRouter()

@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {}
    }
    
    # Check database
    try:
        await db.execute("SELECT 1")
        health_status["services"]["database"] = "healthy"
    except Exception as e:
        health_status["services"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "unhealthy"
    
    # Check LLM service
    try:
        llm_service = LLMService()
        await llm_service.health_check()
        health_status["services"]["llm"] = "healthy"
    except Exception as e:
        health_status["services"]["llm"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"
    
    return health_status
```

## Backup and Recovery

### Database Backup Script

```bash
#!/bin/bash
# scripts/backup.sh

set -e

BACKUP_DIR="/backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="chattrain_backup_${DATE}.sql"

echo "Starting database backup..."

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker-compose exec postgres pg_dump -U $POSTGRES_USER $POSTGRES_DB > $BACKUP_DIR/$BACKUP_FILE

# Compress backup
gzip $BACKUP_DIR/$BACKUP_FILE

# Keep only last 7 days of backups
find $BACKUP_DIR -name "chattrain_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: $BACKUP_DIR/${BACKUP_FILE}.gz"
```

## Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check PostgreSQL status
   docker-compose logs postgres
   
   # Test connection
   docker-compose exec postgres psql -U chattrain -d chattrain_dev -c "SELECT 1;"
   ```

2. **Vector Extension Issues**
   ```sql
   -- Verify pgvector extension
   SELECT * FROM pg_extension WHERE extname = 'vector';
   
   -- Reinstall if needed
   DROP EXTENSION IF EXISTS vector;
   CREATE EXTENSION vector;
   ```

3. **LLM API Issues**
   ```bash
   # Test OpenAI connection
   curl -H "Authorization: Bearer $OPENAI_API_KEY" \
        https://api.openai.com/v1/models
   ```

4. **Frontend Build Issues**
   ```bash
   # Clear node modules and reinstall
   cd src/frontend
   rm -rf node_modules package-lock.json
   npm install
   ```

### Debug Commands

```bash
# View all service logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f backend

# Access database shell
docker-compose exec postgres psql -U chattrain -d chattrain_dev

# Access backend shell
docker-compose exec backend bash

# Check container resource usage
docker stats
```

---

This deployment guide provides comprehensive instructions for setting up ChatTrain MVP1 in both development and production environments with proper containerization, CI/CD, and monitoring capabilities.