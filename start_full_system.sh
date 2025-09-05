#!/bin/bash

# Live Orbital Ballet - Full System Startup Script
# This script starts all components of the satellite tracking system

set -e  # Exit on any error

echo "🚀 Starting Live Orbital Ballet - Complete System"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Checking Docker daemon..."
if ! docker info &> /dev/null; then
    print_error "Docker daemon is not running. Please start Docker first."
    exit 1
fi

print_success "Docker is ready!"

# Clean up any existing containers
print_status "Cleaning up existing containers..."
docker-compose down --remove-orphans 2>/dev/null || true

# Build and start all services
print_status "Building and starting all services..."
docker-compose up --build -d

# Wait for database to be ready
print_status "Waiting for database to be ready..."
timeout=60
while ! docker-compose exec -T database pg_isready -U postgres -d orbital_ballet &> /dev/null; do
    sleep 2
    timeout=$((timeout - 2))
    if [ $timeout -le 0 ]; then
        print_error "Database failed to start within 60 seconds"
        docker-compose logs database
        exit 1
    fi
done

print_success "Database is ready!"

# Initialize database
print_status "Initializing database with sample data..."
docker-compose run --rm db-init

print_success "Database initialized successfully!"

# Wait for applications to be ready
print_status "Waiting for applications to start..."
sleep 10

# Check service health
print_status "Checking service health..."

services=("app-main:8501" "app-enhanced:8502" "app-maneuvering:8503" "app-threejs:8504")
for service in "${services[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    if curl -sf http://localhost:$port/_stcore/health > /dev/null 2>&1; then
        print_success "$name is healthy on port $port"
    else
        print_warning "$name may still be starting on port $port"
    fi
done

# Check WebSocket server
print_status "Checking WebSocket server..."
if nc -z localhost 8765; then
    print_success "WebSocket server is running on port 8765"
else
    print_warning "WebSocket server may still be starting on port 8765"
fi

echo ""
echo "🎉 Live Orbital Ballet System Started Successfully!"
echo "=================================================="
echo ""
echo "📱 Access your applications:"
echo "   🛰️  Main Application (Full System):     http://localhost:8501"
echo "   📊 Enhanced Dashboard:                  http://localhost:8502" 
echo "   🚀 Integrated Maneuvering System:       http://localhost:8503"
echo "   🌍 Three.js 3D Simulation:             http://localhost:8504"
echo ""
echo "🗄️  Database Connection:"
echo "   Host: localhost"
echo "   Port: 5432"
echo "   Database: orbital_ballet"
echo "   Username: postgres"
echo "   Password: postgres"
echo ""
echo "🌐 WebSocket Server:"
echo "   URL: ws://localhost:8765"
echo "   Real-time satellite data streaming"
echo ""
echo "📋 Useful Commands:"
echo "   View logs:           docker-compose logs -f [service_name]"
echo "   Stop system:         docker-compose down"
echo "   Restart service:     docker-compose restart [service_name]"
echo "   Database shell:      docker-compose exec database psql -U postgres -d orbital_ballet"
echo ""
echo "🔍 System Status:"
docker-compose ps

echo ""
print_success "All systems operational! 🚀"