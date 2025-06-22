#!/bin/bash

# start_dev.sh - ChatTrain MVP1 Development Server Startup Script
# This script starts all development services for ChatTrain

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

# Check if .env file exists
check_env() {
    if [ ! -f ".env" ]; then
        error ".env file not found. Please run './scripts/setup.sh' first."
        exit 1
    fi
    
    # Check if OpenAI API key is set
    if ! grep -q "OPENAI_API_KEY=" .env || grep -q "OPENAI_API_KEY=$" .env || grep -q "OPENAI_API_KEY=your_key_here" .env; then
        error "OPENAI_API_KEY is not set in .env file. Please set it before starting."
        exit 1
    fi
    
    success "Environment configuration validated"
}

# Check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
    success "Docker is running"
}

# Stop any existing containers
stop_existing() {
    log "Stopping any existing ChatTrain containers..."
    docker compose down 2>/dev/null || true
    success "Existing containers stopped"
}

# Start development services
start_services() {
    log "Starting ChatTrain development services..."
    
    # Start services in detached mode
    docker compose up -d
    
    log "Waiting for services to be ready..."
    
    # Wait for backend health check
    MAX_RETRIES=30
    RETRY_COUNT=0
    
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
            success "Backend service is ready"
            break
        fi
        
        log "Waiting for backend... (attempt $((RETRY_COUNT + 1))/$MAX_RETRIES)"
        sleep 2
        RETRY_COUNT=$((RETRY_COUNT + 1))
    done
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        error "Backend service failed to start within expected time"
        log "Checking backend logs..."
        docker compose logs backend
        exit 1
    fi
    
    # Wait for frontend
    RETRY_COUNT=0
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if curl -f http://localhost:3000/health > /dev/null 2>&1; then
            success "Frontend service is ready"
            break
        fi
        
        log "Waiting for frontend... (attempt $((RETRY_COUNT + 1))/$MAX_RETRIES)"
        sleep 2
        RETRY_COUNT=$((RETRY_COUNT + 1))
    done
    
    if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
        error "Frontend service failed to start within expected time"
        log "Checking frontend logs..."
        docker compose logs frontend
        exit 1
    fi
}

# Show service status
show_status() {
    log "Service Status:"
    docker compose ps
    echo ""
    
    log "Available endpoints:"
    echo "🌐 Frontend: http://localhost:3000"
    echo "🔗 Backend API: http://localhost:8000"
    echo "📊 API Documentation: http://localhost:8000/docs"
    echo "🗄️ Database: localhost:5432"
    echo "🔴 Redis: localhost:6379"
    echo ""
}

# Show logs
show_logs() {
    if [ "$1" = "--logs" ] || [ "$1" = "-l" ]; then
        log "Following service logs (Ctrl+C to exit)..."
        docker compose logs -f
    else
        log "To view live logs, run: docker compose logs -f"
        log "To view specific service logs, run: docker compose logs -f <service_name>"
    fi
}

# Health check
health_check() {
    log "Running health checks..."
    
    # Check backend health
    if curl -f http://localhost:8000/api/health > /dev/null 2>&1; then
        success "✅ Backend: Healthy"
    else
        error "❌ Backend: Unhealthy"
    fi
    
    # Check frontend health
    if curl -f http://localhost:3000/health > /dev/null 2>&1; then
        success "✅ Frontend: Healthy"
    else
        error "❌ Frontend: Unhealthy"
    fi
    
    # Check database connection
    if docker compose exec -T database pg_isready -U chattrain > /dev/null 2>&1; then
        success "✅ Database: Healthy"
    else
        error "❌ Database: Unhealthy"
    fi
    
    # Check Redis connection
    if docker compose exec -T redis redis-cli ping | grep -q PONG; then
        success "✅ Redis: Healthy"
    else
        error "❌ Redis: Unhealthy"
    fi
}

# Main function
main() {
    log "🚀 Starting ChatTrain MVP1 development environment..."
    
    check_env
    check_docker
    stop_existing
    start_services
    show_status
    health_check
    
    success "🎉 ChatTrain development environment is ready!"
    echo ""
    log "Quick commands:"
    echo "• View logs: docker compose logs -f"
    echo "• Stop services: docker compose down"
    echo "• Restart services: docker compose restart"
    echo "• Run health check: ./scripts/health_check.sh"
    echo ""
    
    show_logs "$1"
}

# Handle command line arguments
case "$1" in
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Options:"
        echo "  --logs, -l    Follow logs after startup"
        echo "  --help, -h    Show this help message"
        echo ""
        echo "This script starts the ChatTrain MVP1 development environment."
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac