#!/bin/bash

# health_check.sh - ChatTrain MVP1 System Health Validation Script
# This script validates the health of all ChatTrain services

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

# Default configuration
PRODUCTION_MODE=false
COMPOSE_FILE="docker-compose.yml"
FRONTEND_URL="http://localhost:3000"
BACKEND_URL="http://localhost:8000"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --prod|-p)
            PRODUCTION_MODE=true
            COMPOSE_FILE="docker-compose.prod.yml"
            FRONTEND_URL="http://localhost"
            BACKEND_URL="http://localhost:8000"
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --prod, -p    Check production environment"
            echo "  --help, -h    Show this help message"
            echo ""
            echo "This script performs comprehensive health checks on ChatTrain services."
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Check if Docker is running
check_docker() {
    log "Checking Docker status..."
    
    if ! docker info > /dev/null 2>&1; then
        error "❌ Docker is not running"
        return 1
    fi
    
    success "✅ Docker is running"
    return 0
}

# Check container status
check_containers() {
    log "Checking container status..."
    
    local failed=0
    
    # Get container status
    while IFS= read -r line; do
        if [[ $line == *"Up"* ]]; then
            success "✅ $(echo $line | awk '{print $1}'): Running"
        else
            error "❌ $(echo $line | awk '{print $1}'): Not running"
            failed=1
        fi
    done < <(docker compose -f "$COMPOSE_FILE" ps --format "table {{.Name}}\t{{.Status}}" | tail -n +2)
    
    return $failed
}

# Check service health endpoints
check_service_health() {
    log "Checking service health endpoints..."
    
    local failed=0
    
    # Check backend health
    log "Checking backend health..."
    if curl -f "$BACKEND_URL/api/health" > /dev/null 2>&1; then
        success "✅ Backend health check passed"
    else
        error "❌ Backend health check failed"
        failed=1
    fi
    
    # Check frontend health (if available)
    log "Checking frontend health..."
    if curl -f "$FRONTEND_URL/health" > /dev/null 2>&1; then
        success "✅ Frontend health check passed"
    else
        warning "⚠️ Frontend health check not available or failed"
    fi
    
    return $failed
}

# Check database connectivity
check_database() {
    log "Checking database connectivity..."
    
    local failed=0
    
    if docker compose -f "$COMPOSE_FILE" exec -T database pg_isready -U chattrain > /dev/null 2>&1; then
        success "✅ Database is accessible"
        
        # Check database connection with query
        if docker compose -f "$COMPOSE_FILE" exec -T database psql -U chattrain -d chattrain -c "SELECT 1;" > /dev/null 2>&1; then
            success "✅ Database query test passed"
        else
            error "❌ Database query test failed"
            failed=1
        fi
    else
        error "❌ Database is not accessible"
        failed=1
    fi
    
    return $failed
}

# Check Redis connectivity
check_redis() {
    log "Checking Redis connectivity..."
    
    local failed=0
    
    if docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping | grep -q PONG; then
        success "✅ Redis is accessible"
        
        # Test basic Redis operations
        if docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli set health_check_test "OK" > /dev/null 2>&1 && \
           docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli get health_check_test | grep -q "OK"; then
            success "✅ Redis read/write test passed"
            docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli del health_check_test > /dev/null 2>&1
        else
            error "❌ Redis read/write test failed"
            failed=1
        fi
    else
        error "❌ Redis is not accessible"
        failed=1
    fi
    
    return $failed
}

# Check API endpoints
check_api_endpoints() {
    log "Checking API endpoints..."
    
    local failed=0
    
    # Check API documentation
    if curl -f "$BACKEND_URL/docs" > /dev/null 2>&1; then
        success "✅ API documentation is accessible"
    else
        error "❌ API documentation is not accessible"
        failed=1
    fi
    
    # Check OpenAPI spec
    if curl -f "$BACKEND_URL/openapi.json" > /dev/null 2>&1; then
        success "✅ OpenAPI specification is accessible"
    else
        error "❌ OpenAPI specification is not accessible"
        failed=1
    fi
    
    return $failed
}

# Check resource usage
check_resource_usage() {
    log "Checking resource usage..."
    
    echo "Container Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}"
    echo ""
    
    # Check for high resource usage
    local high_cpu_containers=$(docker stats --no-stream --format "{{.Container}}\t{{.CPUPerc}}" | awk '$2 > 80 {print $1}')
    local high_mem_containers=$(docker stats --no-stream --format "{{.Container}}\t{{.MemPerc}}" | awk '$2 > 80 {print $1}')
    
    if [ -n "$high_cpu_containers" ]; then
        warning "⚠️ High CPU usage detected in containers: $high_cpu_containers"
    fi
    
    if [ -n "$high_mem_containers" ]; then
        warning "⚠️ High memory usage detected in containers: $high_mem_containers"
    fi
}

# Check disk usage
check_disk_usage() {
    log "Checking disk usage..."
    
    # Check Docker volumes
    docker system df
    echo ""
    
    # Check for low disk space
    local disk_usage=$(df -h . | awk 'NR==2 {print $5}' | sed 's/%//')
    
    if [ "$disk_usage" -gt 90 ]; then
        error "❌ Critical disk space: ${disk_usage}% used"
    elif [ "$disk_usage" -gt 80 ]; then
        warning "⚠️ Low disk space: ${disk_usage}% used"
    else
        success "✅ Disk space OK: ${disk_usage}% used"
    fi
}

# Check logs for errors
check_logs() {
    log "Checking recent logs for errors..."
    
    local error_count=0
    
    # Check backend logs for errors
    local backend_errors=$(docker compose -f "$COMPOSE_FILE" logs --tail=100 backend 2>/dev/null | grep -i error | wc -l)
    if [ "$backend_errors" -gt 0 ]; then
        warning "⚠️ Found $backend_errors error(s) in backend logs"
        error_count=$((error_count + backend_errors))
    fi
    
    # Check frontend logs for errors
    local frontend_errors=$(docker compose -f "$COMPOSE_FILE" logs --tail=100 frontend 2>/dev/null | grep -i error | wc -l)
    if [ "$frontend_errors" -gt 0 ]; then
        warning "⚠️ Found $frontend_errors error(s) in frontend logs"
        error_count=$((error_count + frontend_errors))
    fi
    
    # Check database logs for errors
    local db_errors=$(docker compose -f "$COMPOSE_FILE" logs --tail=100 database 2>/dev/null | grep -i error | wc -l)
    if [ "$db_errors" -gt 0 ]; then
        warning "⚠️ Found $db_errors error(s) in database logs"
        error_count=$((error_count + db_errors))
    fi
    
    if [ "$error_count" -eq 0 ]; then
        success "✅ No recent errors found in logs"
    else
        warning "⚠️ Total errors found in logs: $error_count"
    fi
}

# Generate health report
generate_report() {
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    local mode=$([ "$PRODUCTION_MODE" = true ] && echo "Production" || echo "Development")
    
    echo ""
    log "=== ChatTrain Health Check Report ($mode Mode) ==="
    echo "Timestamp: $timestamp"
    echo "Environment: $mode"
    echo "Compose File: $COMPOSE_FILE"
    echo "Frontend URL: $FRONTEND_URL"
    echo "Backend URL: $BACKEND_URL"
    echo ""
    
    if [ $1 -eq 0 ]; then
        success "🎉 Overall Health Status: HEALTHY"
    else
        error "❌ Overall Health Status: UNHEALTHY ($1 issues found)"
    fi
    
    echo ""
    log "For detailed logs, run:"
    echo "docker compose -f $COMPOSE_FILE logs -f"
}

# Main health check function
main() {
    local total_failures=0
    
    if [ "$PRODUCTION_MODE" = true ]; then
        log "🔍 Running ChatTrain Production Health Check..."
    else
        log "🔍 Running ChatTrain Development Health Check..."
    fi
    
    echo ""
    
    # Run all health checks
    check_docker || total_failures=$((total_failures + 1))
    echo ""
    
    check_containers || total_failures=$((total_failures + 1))
    echo ""
    
    check_service_health || total_failures=$((total_failures + 1))
    echo ""
    
    check_database || total_failures=$((total_failures + 1))
    echo ""
    
    check_redis || total_failures=$((total_failures + 1))
    echo ""
    
    check_api_endpoints || total_failures=$((total_failures + 1))
    echo ""
    
    check_resource_usage
    echo ""
    
    check_disk_usage
    echo ""
    
    check_logs
    echo ""
    
    generate_report $total_failures
    
    exit $total_failures
}

# Run main function
main "$@"