#!/bin/bash

# Intelligent Data Quality Platform - Setup Script
# This script sets up the complete development environment

set -e

echo "🚀 Setting up Intelligent Data Quality Platform..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    print_status "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check Node.js (for local development)
    if ! command -v node &> /dev/null; then
        print_warning "Node.js is not installed. You won't be able to run frontend locally."
    fi
    
    # Check Python (for local development)
    if ! command -v python3 &> /dev/null; then
        print_warning "Python 3 is not installed. You won't be able to run backend locally."
    fi
    
    print_success "Prerequisites check completed"
}

# Create necessary directories
create_directories() {
    print_status "Creating necessary directories..."
    
    mkdir -p data/raw
    mkdir -p data/processed
    mkdir -p data/delta-lake
    mkdir -p logs
    mkdir -p tmp
    mkdir -p examples/sample_data
    
    print_success "Directories created"
}

# Generate environment files
generate_env_files() {
    print_status "Generating environment files..."
    
    # Backend .env
    cat > backend/.env << EOF
# Backend Configuration
DEBUG=true
SECRET_KEY=your-secret-key-change-in-production
ACCESS_TOKEN_EXPIRE_MINUTES=480

# Database
POSTGRES_SERVER=localhost
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=data_quality
POSTGRES_PORT=5432

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Spark
SPARK_MASTER=local[*]
SPARK_SQL_WAREHOUSE_DIR=/tmp/spark-warehouse
DELTA_LAKE_PATH=/tmp/delta-lake

# Kafka
KAFKA_BOOTSTRAP_SERVERS=localhost:9092

# MLflow
MLFLOW_TRACKING_URI=http://localhost:5000

# Storage
DATA_STORAGE_PATH=/tmp/data-quality-storage

# Alerts
ALERT_EMAIL_ENABLED=true
ALERT_SLACK_ENABLED=false
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_TLS=true
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Monitoring
ENABLE_METRICS=true
PROMETHEUS_PORT=8080
EOF

    # Frontend .env
    cat > frontend/.env << EOF
# Frontend Configuration
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_ENVIRONMENT=development
EOF

    print_success "Environment files generated"
}

# Create sample data
create_sample_data() {
    print_status "Creating sample data..."
    
    # Create sample CSV data
    cat > examples/sample_data/customer_transactions.csv << EOF
transaction_id,customer_id,amount,timestamp,merchant,category
txn_001,cust_123,99.99,2024-01-14T10:30:00Z,Amazon,retail
txn_002,cust_456,45.67,2024-01-14T11:15:00Z,Starbucks,food
txn_003,cust_789,199.99,2024-01-14T12:00:00Z,Best Buy,electronics
txn_004,cust_123,25.50,2024-01-14T13:30:00Z,Uber,transport
txn_005,cust_456,89.99,2024-01-14T14:45:00Z,Target,retail
EOF

    # Create sample user events JSON
    cat > examples/sample_data/user_events.json << EOF
[
  {
    "event_id": "evt_001",
    "user_id": "user_123",
    "event_type": "page_view",
    "timestamp": "2024-01-14T10:30:00Z",
    "properties": {
      "page": "/dashboard",
      "source": "organic"
    }
  },
  {
    "event_id": "evt_002",
    "user_id": "user_456",
    "event_type": "button_click",
    "timestamp": "2024-01-14T10:31:00Z",
    "properties": {
      "button": "export_data",
      "page": "/reports"
    }
  }
]
EOF

    print_success "Sample data created"
}

# Initialize Docker services
init_docker_services() {
    print_status "Initializing Docker services..."
    
    # Pull required images
    print_status "Pulling Docker images..."
    docker-compose pull
    
    # Start services
    print_status "Starting services..."
    docker-compose up -d
    
    # Wait for services to be ready
    print_status "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_service_health
    
    print_success "Docker services initialized"
}

# Check service health
check_service_health() {
    print_status "Checking service health..."
    
    # Check backend
    if curl -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "Backend service is healthy"
    else
        print_warning "Backend service is not responding"
    fi
    
    # Check frontend
    if curl -f http://localhost:3000 > /dev/null 2>&1; then
        print_success "Frontend service is healthy"
    else
        print_warning "Frontend service is not responding"
    fi
    
    # Check PostgreSQL
    if docker-compose exec -T postgres pg_isready > /dev/null 2>&1; then
        print_success "PostgreSQL is ready"
    else
        print_warning "PostgreSQL is not ready"
    fi
}

# Setup development environment
setup_dev_environment() {
    print_status "Setting up development environment..."
    
    # Install backend dependencies
    if command -v python3 &> /dev/null; then
        print_status "Installing Python dependencies..."
        cd backend
        python3 -m pip install -r requirements.txt
        cd ..
        print_success "Python dependencies installed"
    fi
    
    # Install frontend dependencies
    if command -v npm &> /dev/null; then
        print_status "Installing Node.js dependencies..."
        cd frontend
        npm install
        cd ..
        print_success "Node.js dependencies installed"
    fi
}

# Create Makefile for easy commands
create_makefile() {
    print_status "Creating Makefile..."
    
    cat > Makefile << 'EOF'
# Intelligent Data Quality Platform - Makefile

.PHONY: help setup dev-up dev-down test clean logs

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

setup: ## Initial setup
	@echo "🚀 Setting up Intelligent Data Quality Platform..."
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

deploy: ## Deploy to production
	@echo "🚀 Deploying to production..."
	docker-compose -f docker-compose.prod.yml up -d
EOF

    print_success "Makefile created"
}

# Print completion message
print_completion() {
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "📋 What's been set up:"
    echo "   ✅ Docker services (PostgreSQL, Redis, Kafka, Spark, MLflow)"
    echo "   ✅ Backend API with FastAPI"
    echo "   ✅ Frontend React application"
    echo "   ✅ Monitoring with Prometheus & Grafana"
    echo "   ✅ Sample data for testing"
    echo "   ✅ Development environment"
    echo ""
    echo "🚀 Quick start:"
    echo "   make dev-up    # Start all services"
    echo "   make logs      # View logs"
    echo "   make help      # See all commands"
    echo ""
    echo "🌐 Access URLs:"
    echo "   Frontend:      http://localhost:3000"
    echo "   Backend API:   http://localhost:8000"
    echo "   API Docs:      http://localhost:8000/docs"
    echo "   Grafana:       http://localhost:3001 (admin/admin)"
    echo "   Spark UI:      http://localhost:8080"
    echo "   MLflow:        http://localhost:5000"
    echo ""
    echo "🔥 Happy coding with the Data Quality Platform!"
}

# Main execution
main() {
    check_prerequisites
    create_directories
    generate_env_files
    create_sample_data
    create_makefile
    setup_dev_environment
    init_docker_services
    print_completion
}

# Run main function
main "$@"
