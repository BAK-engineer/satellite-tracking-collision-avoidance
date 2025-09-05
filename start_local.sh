#!/bin/bash

# Live Orbital Ballet - Local Development Startup
# Run the complete system locally without Docker

set -e

echo "🚀 Starting Live Orbital Ballet - Local Development Mode"
echo "======================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

# Check Python installation
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed"
    exit 1
fi

print_success "Python 3 found: $(python3 --version)"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    print_status "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
print_status "Activating virtual environment..."
source venv/bin/activate

# Install requirements
print_status "Installing/updating requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# Check if PostgreSQL is running (optional for local development)
if command -v pg_isready &> /dev/null; then
    if pg_isready -h localhost -p 5432 &> /dev/null; then
        print_success "PostgreSQL database detected and running"
        export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/orbital_ballet'
        
        # Initialize database if needed
        print_status "Setting up database..."
        python setup_database.py --create-tables --sample-data
    else
        print_warning "PostgreSQL not running. Starting database with Docker..."
        if command -v docker &> /dev/null; then
            docker run -d --name orbital-postgres \
                -e POSTGRES_DB=orbital_ballet \
                -e POSTGRES_USER=postgres \
                -e POSTGRES_PASSWORD=postgres \
                -p 5432:5432 postgres:13 2>/dev/null || true
            
            print_status "Waiting for database to start..."
            sleep 10
            
            export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/orbital_ballet'
            python setup_database.py --create-tables --sample-data
        else
            print_warning "Docker not found. Running without database integration."
        fi
    fi
else
    print_warning "PostgreSQL not found. Running without database integration."
fi

echo ""
echo "🎯 Choose which application to run:"
echo "1. Main Application (Full System with all components)"
echo "2. Enhanced Dashboard (Database integrated)"
echo "3. Integrated Maneuvering System (Visual maneuvers)"
echo "4. Basic UI (Original satellite tracking)"
echo "5. Run All Applications (in separate terminals)"
echo ""

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        print_success "Starting Main Application (Full System)..."
        echo "Access at: http://localhost:8501"
        streamlit run app.py --server.address 0.0.0.0 --server.port 8501
        ;;
    2)
        print_success "Starting Enhanced Dashboard..."
        echo "Access at: http://localhost:8502"
        streamlit run ui_enhanced.py --server.address 0.0.0.0 --server.port 8502
        ;;
    3)
        print_success "Starting Integrated Maneuvering System..."
        echo "Access at: http://localhost:8503"
        streamlit run ui_integrated.py --server.address 0.0.0.0 --server.port 8503
        ;;
    4)
        print_success "Starting Basic UI..."
        echo "Access at: http://localhost:8504"
        streamlit run ui.py --server.address 0.0.0.0 --server.port 8504
        ;;
    5)
        print_success "Starting all applications..."
        echo ""
        echo "🌐 Application URLs:"
        echo "   Main System:      http://localhost:8501"
        echo "   Enhanced:         http://localhost:8502"
        echo "   Maneuvering:      http://localhost:8503"
        echo "   Basic UI:         http://localhost:8504"
        echo ""
        
        # Start all in background
        streamlit run app.py --server.address 0.0.0.0 --server.port 8501 &
        sleep 3
        streamlit run ui_enhanced.py --server.address 0.0.0.0 --server.port 8502 &
        sleep 3
        streamlit run ui_integrated.py --server.address 0.0.0.0 --server.port 8503 &
        sleep 3
        streamlit run ui.py --server.address 0.0.0.0 --server.port 8504 &
        
        print_success "All applications started!"
        echo "Press Ctrl+C to stop all applications"
        wait
        ;;
    *)
        print_error "Invalid choice. Please run the script again."
        exit 1
        ;;
esac