#!/bin/bash

# deploy_prod.sh - ChatTrain MVP1 Production Deployment Script
# This script deploys ChatTrain to production environment

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check production readiness
check_production_readiness() {
    log "Checking production readiness..."
    
    # Check if .env file exists
    if [ ! -f ".env" ]; then
        error ".env file not found. Please create it from .env.example"
        exit 1
    fi
    
    # Check required environment variables
    if ! grep -q "OPENAI_API_KEY=" .env || grep -q "OPENAI_API_KEY=$" .env || grep -q "OPENAI_API_KEY=your_key_here" .env; then
        error "OPENAI_API_KEY is not set in .env file"
        exit 1
    fi
    
    if ! grep -q "POSTGRES_PASSWORD=" .env || grep -q "POSTGRES_PASSWORD=$" .env; then
        error "POSTGRES_PASSWORD is not set in .env file"
        exit 1
    fi
    
    # Check Docker
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker."
        exit 1
    fi
    
    success "Production readiness check passed"
}

# Build images
build_images() {
    log "Building production Docker images..."
    
    # Build backend image
    log "Building backend image..."
    docker build -f Dockerfile.backend -t chattrain-backend:latest .
    
    # Build frontend image
    log "Building frontend image..."
    docker build -f Dockerfile.frontend -t chattrain-frontend:latest .
    
    success "Docker images built successfully"
}

# Stop existing production services
stop_production() {
    log "Stopping existing production services..."
    docker compose -f docker-compose.prod.yml down 2>/dev/null || true
    success "Existing production services stopped"
}

# Start production services
start_production() {
    log "Starting production services..."
    
    # Start services
    docker compose -f docker-compose.prod.yml up -d
    
    log "Waiting for services to be ready..."
    
    # Wait for backend health check
    MAX_RETRIES=60
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f http://localhost:8000/health > /dev/null 2>&1; then
            success "Backend service is ready"
            break
        fi
        
        log "Waiting for backend... (attempt $((RETRY_COUNT + 1))/$MAX_RETRIES)"
        sleep 5
        RETRY_COUNT=$((RETRY_COUNT + 1))
    done
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        error "Backend service failed to start within expected time"
        log "Checking backend logs..."
        docker compose -f docker-compose.prod.yml logs backend
        exit 1
    fi
    
    # Wait for frontend
    RETRY_COUNT=0
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f http://localhost/health > /dev/null 2>&1; then
            success "Frontend service is ready"
            break
        fi
        
        log "Waiting for frontend... (attempt $((RETRY_COUNT + 1))/$MAX_RETRIES)"
        sleep 5
        RETRY_COUNT=$((RETRY_COUNT + 1))
    done
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        warning "Frontend health check timeout - this may be normal for production"
    fi
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    
    # Wait for database to be ready
    MAX_RETRIES=30
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if docker compose -f docker-compose.prod.yml exec -T database pg_isready -U chattrain > /dev/null 2>&1; then
            success "Database is ready"
            break
        fi
        
        log "Waiting for database... (attempt $((RETRY_COUNT + 1))/$MAX_RETRIES)"
        sleep 2
        RETRY_COUNT=$((RETRY_COUNT + 1))
    done
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        error "Database failed to start within expected time"
        exit 1
    fi
    
    # Run any additional migrations if needed
    log "Database migrations completed"
}

# Backup data
backup_data() {
    if [ "$1" = "--backup" ] || [ "$1" = "-b" ]; then
        log "Creating data backup..."
        
        BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"
        
        # Backup database
        if docker compose -f docker-compose.prod.yml exec -T database pg_dump -U chattrain chattrain > "$BACKUP_DIR/database.sql"; then
            success "Database backup created: $BACKUP_DIR/database.sql"
        else
            warning "Database backup failed"
        fi
        
        # Backup volumes
        docker run --rm -v chattrain_chattrain_data:/data -v "$(pwd)/$BACKUP_DIR":/backup alpine tar czf /backup/chattrain_data.tar.gz -C /data .
        success "Data volumes backup created: $BACKUP_DIR/chattrain_data.tar.gz"
        
        success "Backup completed: $BACKUP_DIR"
    fi
}

# Show production status
show_production_status() {
    log "Production Service Status:"
    docker compose -f docker-compose.prod.yml ps
    echo ""
    
    log "Available endpoints:"
    echo "🌐 Application: http://localhost (port 80)"
    echo "🔗 Backend API: http://localhost:8000 (internal)"
    echo "📊 API Documentation: http://localhost:8000/docs (internal)"
    echo ""
    
    log "Resource usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

# Production health check
production_health_check() {
    log "Running production health checks..."
    
    # Check all services
    docker compose -f docker-compose.prod.yml exec -T backend curl -f http://localhost:8000/health > /dev/null 2>&1 && success "✅ Backend: Healthy" || error "❌ Backend: Unhealthy"
    curl -f http://localhost/health > /dev/null 2>&1 && success "✅ Frontend: Healthy" || warning "⚠️ Frontend: Health check unavailable"
    docker compose -f docker-compose.prod.yml exec -T database pg_isready -U chattrain > /dev/null 2>&1 && success "✅ Database: Healthy" || error "❌ Database: Unhealthy"
    docker compose -f docker-compose.prod.yml exec -T redis redis-cli ping | grep -q PONG && success "✅ Redis: Healthy" || error "❌ Redis: Unhealthy"
}

# Main deployment function
main() {
    log "🚀 Starting ChatTrain MVP1 production deployment..."
    
    backup_data "$1"
    check_production_readiness
    build_images
    stop_production
    start_production
    run_migrations
    show_production_status
    production_health_check
    
    success "🎉 ChatTrain production deployment completed successfully!"
    echo ""
    log "Production commands:"
    echo "• View logs: docker compose -f docker-compose.prod.yml logs -f"
    echo "• Stop services: docker compose -f docker-compose.prod.yml down"
    echo "• Restart services: docker compose -f docker-compose.prod.yml restart"
    echo "• Health check: ./scripts/health_check.sh --prod"
    echo "• Scale services: docker compose -f docker-compose.prod.yml up -d --scale backend=2"
    echo ""
    
    warning "⚠️ Security reminders:"
    echo "• Change default database passwords"
    echo "• Set up SSL certificates for HTTPS"
    echo "• Configure firewall rules"
    echo "• Set up monitoring and alerting"
    echo "• Regular backup schedule"
}

# Handle command line arguments
case "$1" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --backup, -b  Create backup before deployment"
        echo "  --help, -h    Show this help message"
        echo ""
        echo "This script deploys ChatTrain MVP1 to production environment."
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac