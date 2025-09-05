#!/bin/bash

# 🚀 ORBITAL NEXUS - Professional Deployment Script
# Automated deployment for production environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="orbital-nexus"
DOCKER_REGISTRY="ghcr.io/orbital-nexus"
VERSION=${1:-"latest"}
ENVIRONMENT=${2:-"production"}

print_header() {
    echo -e "${BLUE}"
    echo "🛰️  ======================================"
    echo "    ORBITAL NEXUS DEPLOYMENT SCRIPT"
    echo "    Version: $VERSION"
    echo "    Environment: $ENVIRONMENT"
    echo "======================================${NC}"
}

print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    print_status "Checking deployment requirements..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check environment file
    if [ ! -f ".env" ]; then
        print_warning ".env file not found, copying from .env.example"
        if [ -f ".env.example" ]; then
            cp .env.example .env
        else
            print_error ".env.example not found"
            exit 1
        fi
    fi
    
    print_status "✅ All requirements satisfied"
}

setup_directories() {
    print_status "Setting up directories..."
    
    # Create required directories
    mkdir -p logs
    mkdir -p data/postgres
    mkdir -p data/redis
    mkdir -p monitoring/prometheus
    mkdir -p monitoring/grafana
    mkdir -p ssl
    
    # Set permissions
    chmod 755 logs data monitoring ssl
    
    print_status "✅ Directories created"
}

build_images() {
    print_status "Building Docker images..."
    
    # Build backend
    print_status "Building backend image..."
    docker build -t ${DOCKER_REGISTRY}/backend:${VERSION} ./backend
    
    # Build frontend
    print_status "Building frontend image..."
    docker build -t ${DOCKER_REGISTRY}/frontend:${VERSION} ./frontend
    
    print_status "✅ Images built successfully"
}

push_images() {
    if [ "$ENVIRONMENT" = "production" ]; then
        print_status "Pushing images to registry..."
        
        docker push ${DOCKER_REGISTRY}/backend:${VERSION}
        docker push ${DOCKER_REGISTRY}/frontend:${VERSION}
        
        print_status "✅ Images pushed to registry"
    else
        print_status "Skipping image push for $ENVIRONMENT environment"
    fi
}

setup_database() {
    print_status "Setting up database..."
    
    # Start PostgreSQL container
    docker-compose up -d postgres
    
    # Wait for database to be ready
    print_status "Waiting for database to be ready..."
    sleep 10
    
    # Run database migrations
    print_status "Running database migrations..."
    docker-compose run --rm backend python -c "
from main import Base, engine
Base.metadata.create_all(bind=engine)
print('✅ Database tables created')
"
    
    print_status "✅ Database setup complete"
}

deploy_services() {
    print_status "Deploying services..."
    
    # Set environment variables
    export VERSION=$VERSION
    export ENVIRONMENT=$ENVIRONMENT
    
    # Deploy based on environment
    if [ "$ENVIRONMENT" = "production" ]; then
        docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
    else
        docker-compose up -d
    fi
    
    print_status "✅ Services deployed"
}

run_health_checks() {
    print_status "Running health checks..."
    
    # Wait for services to be ready
    sleep 30
    
    # Check backend health
    print_status "Checking backend health..."
    if curl -f http://localhost:8000/ > /dev/null 2>&1; then
        print_status "✅ Backend is healthy"
    else
        print_error "❌ Backend health check failed"
        docker-compose logs backend
        exit 1
    fi
    
    # Check frontend health
    print_status "Checking frontend health..."
    if curl -f http://localhost:3000/ > /dev/null 2>&1; then
        print_status "✅ Frontend is healthy"
    else
        print_error "❌ Frontend health check failed"
        docker-compose logs frontend
        exit 1
    fi
    
    # Check database connection
    print_status "Checking database connection..."
    if docker-compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
        print_status "✅ Database is healthy"
    else
        print_error "❌ Database health check failed"
        exit 1
    fi
    
    print_status "✅ All health checks passed"
}

setup_ssl() {
    if [ "$ENVIRONMENT" = "production" ]; then
        print_status "Setting up SSL certificates..."
        
        # Check if SSL certificates exist
        if [ ! -f "ssl/cert.pem" ] || [ ! -f "ssl/key.pem" ]; then
            print_warning "SSL certificates not found"
            print_status "Generating self-signed certificates for development..."
            
            openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
                -keyout ssl/key.pem \
                -out ssl/cert.pem \
                -subj "/C=US/ST=Space/L=Orbit/O=OrbitalNexus/CN=localhost"
        fi
        
        print_status "✅ SSL certificates ready"
    fi
}

setup_monitoring() {
    print_status "Setting up monitoring..."
    
    # Copy monitoring configurations
    if [ ! -f "monitoring/prometheus.yml" ]; then
        cat > monitoring/prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: 'orbital-nexus-backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'
    scrape_interval: 5s

  - job_name: 'orbital-nexus-postgres'
    static_configs:
      - targets: ['postgres:5432']

  - job_name: 'orbital-nexus-redis'
    static_configs:
      - targets: ['redis:6379']
EOF
    fi
    
    # Set up Grafana dashboards
    mkdir -p monitoring/grafana/dashboards
    mkdir -p monitoring/grafana/datasources
    
    # Grafana datasource configuration
    cat > monitoring/grafana/datasources/prometheus.yml << EOF
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
EOF
    
    print_status "✅ Monitoring setup complete"
}

show_deployment_info() {
    print_header
    print_status "🎉 Deployment completed successfully!"
    echo ""
    print_status "📊 Service URLs:"
    echo "  🌐 Frontend:    http://localhost:3000"
    echo "  📡 Backend API: http://localhost:8000"
    echo "  📊 Grafana:     http://localhost:3001 (admin/orbital_admin_2024)"
    echo "  🔍 Prometheus:  http://localhost:9090"
    echo ""
    print_status "🔧 Management Commands:"
    echo "  View logs:      docker-compose logs -f"
    echo "  Stop services:  docker-compose down"
    echo "  Update:         ./deploy.sh [version] [environment]"
    echo ""
    print_status "📈 Monitor your deployment:"
    echo "  Health:         curl http://localhost:8000/health"
    echo "  Metrics:        curl http://localhost:8000/metrics"
    echo "  Status:         docker-compose ps"
    echo ""
}

backup_data() {
    if [ "$ENVIRONMENT" = "production" ]; then
        print_status "Creating data backup..."
        
        # Create backup directory
        BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p $BACKUP_DIR
        
        # Backup database
        docker-compose exec -T postgres pg_dump -U postgres orbital_nexus > $BACKUP_DIR/database.sql
        
        # Backup configuration
        cp .env $BACKUP_DIR/
        cp docker-compose.yml $BACKUP_DIR/
        
        print_status "✅ Backup created in $BACKUP_DIR"
    fi
}

rollback() {
    print_warning "Rolling back deployment..."
    
    # Stop current services
    docker-compose down
    
    # Get previous version
    PREVIOUS_VERSION=$(docker images --format "table {{.Repository}}:{{.Tag}}" | grep ${DOCKER_REGISTRY} | head -2 | tail -1 | cut -d: -f2)
    
    if [ -n "$PREVIOUS_VERSION" ]; then
        print_status "Rolling back to version: $PREVIOUS_VERSION"
        VERSION=$PREVIOUS_VERSION deploy_services
        print_status "✅ Rollback completed"
    else
        print_error "No previous version found for rollback"
        exit 1
    fi
}

cleanup() {
    print_status "Cleaning up old images and containers..."
    
    # Remove old images (keep last 3 versions)
    docker images ${DOCKER_REGISTRY}/backend --format "table {{.ID}}" | tail -n +4 | xargs -r docker rmi
    docker images ${DOCKER_REGISTRY}/frontend --format "table {{.ID}}" | tail -n +4 | xargs -r docker rmi
    
    # Remove unused containers and networks
    docker system prune -f
    
    print_status "✅ Cleanup completed"
}

# Main deployment flow
main() {
    print_header
    
    case ${3:-"deploy"} in
        "deploy")
            check_requirements
            setup_directories
            setup_ssl
            backup_data
            build_images
            push_images
            setup_database
            setup_monitoring
            deploy_services
            run_health_checks
            show_deployment_info
            ;;
        "rollback")
            rollback
            ;;
        "cleanup")
            cleanup
            ;;
        "health")
            run_health_checks
            ;;
        *)
            echo "Usage: $0 [version] [environment] [action]"
            echo "Actions: deploy (default), rollback, cleanup, health"
            exit 1
            ;;
    esac
}

# Error handling
trap 'print_error "Deployment failed at line $LINENO"' ERR

# Run main function
main "$@"