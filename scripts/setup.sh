#!/bin/bash

# setup.sh - ChatTrain MVP1 Environment Setup Script
# This script sets up the complete development environment for ChatTrain

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
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

# Check if running on macOS
check_macos() {
    if [[ "$OSTYPE" != "darwin"* ]]; then
        error "This script is designed for macOS. Please adjust for your operating system."
        exit 1
    fi
    success "Running on macOS"
}

# Check required tools
check_requirements() {
    log "Checking system requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed. Please install Docker Desktop from https://www.docker.com/products/docker-desktop"
        exit 1
    fi
    
    # Check Docker Compose
    if ! docker compose version &> /dev/null; then
        error "Docker Compose is not available. Please update Docker Desktop."
        exit 1
    fi
    
    # Check Node.js
    if ! command -v node &> /dev/null; then
        error "Node.js is not installed. Please install Node.js 20+ from https://nodejs.org/"
        exit 1
    fi
    
    # Check Node version
    NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
    if [ "$NODE_VERSION" -lt 20 ]; then
        error "Node.js version 20 or higher is required. Current version: $(node -v)"
        exit 1
    fi
    
    # Check Python
    if ! command -v python3 &> /dev/null; then
        error "Python 3.11+ is not installed. Please install Python 3.11+ from https://python.org/"
        exit 1
    fi
    
    # Check Python version - prefer Python 3.11
    if command -v python3.11 &> /dev/null; then
        PYTHON_CMD="python3.11"
        PYTHON_VERSION=$(python3.11 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        success "Found Python 3.11: $PYTHON_VERSION"
    elif command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
        PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
        if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 11) else 1)"; then
            error "Python 3.11+ is required. Current version: $PYTHON_VERSION"
            error "Please install Python 3.11: brew install python@3.11"
            exit 1
        fi
        success "Found Python 3: $PYTHON_VERSION"
    else
        error "Python 3.11+ is not installed. Please install Python 3.11+ from https://python.org/"
        exit 1
    fi
    
    success "All system requirements met"
}

# Setup environment file
setup_environment() {
    log "Setting up environment configuration..."
    
    if [ ! -f ".env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example .env
            log "Created .env file from .env.example"
        else
            warning ".env.example not found. You'll need to create .env manually."
        fi
    else
        log ".env file already exists"
    fi
    
    # Check if OpenAI API key is set
    if [ -f ".env" ]; then
        if ! grep -q "OPENAI_API_KEY=" .env || grep -q "OPENAI_API_KEY=$" .env || grep -q "OPENAI_API_KEY=your_key_here" .env; then
            warning "Please set your OPENAI_API_KEY in the .env file"
            warning "You can get an API key from: https://platform.openai.com/api-keys"
        fi
    fi
}

# Setup backend
setup_backend() {
    log "Setting up backend environment..."
    
    cd src/backend
    
    # Create virtual environment if it doesn't exist
    if [ ! -d "venv" ]; then
        log "Creating Python virtual environment..."
        $PYTHON_CMD -m venv venv
    fi
    
    # Activate virtual environment and install dependencies
    log "Installing Python dependencies..."
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    cd ../..
    success "Backend setup completed"
}

# Setup frontend
setup_frontend() {
    log "Setting up frontend environment..."
    
    cd src/frontend
    
    # Install npm dependencies
    log "Installing Node.js dependencies..."
    npm install
    
    cd ../..
    success "Frontend setup completed"
}

# Initialize database
init_database() {
    log "Initializing database..."
    
    # Create database initialization script if it doesn't exist
    if [ ! -f "scripts/init_db.sql" ]; then
        log "Creating database initialization script..."
        cat > scripts/init_db.sql << 'EOF'
-- ChatTrain MVP1 Database Initialization
CREATE EXTENSION IF NOT EXISTS vector;

-- Create tables
CREATE TABLE IF NOT EXISTS sessions (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    scenario_id VARCHAR(255) NOT NULL,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    role VARCHAR(50) NOT NULL,
    content TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    metadata JSONB
);

CREATE TABLE IF NOT EXISTS feedback (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    score INTEGER,
    positive_points TEXT,
    improvement_points TEXT,
    overall_feedback TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_scenario_id ON sessions(scenario_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON messages(session_id);
CREATE INDEX IF NOT EXISTS idx_feedback_session_id ON feedback(session_id);
EOF
    fi
}

# Create necessary directories
create_directories() {
    log "Creating necessary directories..."
    
    mkdir -p data
    mkdir -p logs
    mkdir -p ssl  # For production SSL certificates
    
    success "Directories created"
}

# Set permissions
set_permissions() {
    log "Setting script permissions..."
    
    chmod +x scripts/*.sh
    
    success "Permissions set"
}

# Main setup function
main() {
    log "Starting ChatTrain MVP1 setup..."
    
    check_macos
    check_requirements
    create_directories
    setup_environment
    init_database
    setup_backend
    setup_frontend
    set_permissions
    
    success "🎉 ChatTrain MVP1 setup completed successfully!"
    echo ""
    log "Next steps:"
    echo "1. Edit .env file and set your OPENAI_API_KEY"
    echo "2. Run 'make dev' or './scripts/start_dev.sh' to start development servers"
    echo "3. Visit http://localhost:3000 to access the application"
    echo ""
    log "For more information, see README.md"
}

# Run main function
main "$@"