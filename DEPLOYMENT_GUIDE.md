# 🚀 Live Orbital Ballet - Complete Deployment Guide

## 📋 Overview

This guide covers all methods to run your complete Live Orbital Ballet satellite tracking system with backend database and all components.

## 🏗️ System Architecture

Your complete system includes:
- **PostgreSQL Database** - Enterprise data storage
- **Main Application** (`app.py`) - Full orchestrated system
- **Enhanced Dashboard** (`ui_enhanced.py`) - Database-integrated analytics  
- **Maneuvering System** (`ui_integrated.py`) - Visual maneuver execution
- **Basic UI** (`ui.py`) - Original satellite tracking

## 🎯 Deployment Options

### Option 1: Full Docker Deployment (RECOMMENDED)

**Best for: Production deployment, complete isolation, team development**

#### Prerequisites
- Docker 20.0+ installed
- Docker Compose 2.0+ installed
- 8GB RAM minimum (16GB recommended)
- 20GB disk space

#### Quick Start
```bash
# 1. Start complete system
./start_full_system.sh

# 2. Access applications
# Main System:      http://localhost:8501
# Enhanced:         http://localhost:8502  
# Maneuvering:      http://localhost:8503
```

#### Manual Docker Steps
```bash
# 1. Build and start all services
docker-compose up --build -d

# 2. Initialize database
docker-compose run --rm db-init

# 3. Check status
docker-compose ps

# 4. View logs
docker-compose logs -f
```

#### Docker Services
- `database` - PostgreSQL on port 5432
- `app-main` - Full system on port 8501
- `app-enhanced` - Enhanced dashboard on port 8502  
- `app-maneuvering` - Maneuvering system on port 8503
- `db-init` - One-time database setup

---

### Option 2: Local Development Mode

**Best for: Development, testing, quick start**

#### Prerequisites
- Python 3.8+ installed
- PostgreSQL 13+ (optional, can use Docker)
- 4GB RAM minimum

#### Quick Start
```bash
# 1. Run interactive startup
./start_local.sh

# 2. Choose your application:
#    1 = Main Application (Full System)
#    2 = Enhanced Dashboard  
#    3 = Maneuvering System
#    4 = Basic UI
#    5 = All Applications
```

#### Manual Local Steps
```bash
# 1. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Start database (if using Docker)
docker run -d --name orbital-postgres \
  -e POSTGRES_DB=orbital_ballet \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 postgres:13

# 4. Setup database
export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/orbital_ballet'
python setup_database.py --create-tables --sample-data

# 5. Run application
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

---

### Option 3: Individual Component Deployment

**Best for: Testing specific components, debugging**

#### Main Application (Full System)
```bash
streamlit run app.py --server.address 0.0.0.0 --server.port 8501
```

#### Enhanced Dashboard
```bash  
streamlit run ui_enhanced.py --server.address 0.0.0.0 --server.port 8502
```

#### Maneuvering System
```bash
streamlit run ui_integrated.py --server.address 0.0.0.0 --server.port 8503
```

#### Basic UI
```bash
streamlit run ui.py --server.address 0.0.0.0 --server.port 8504
```

---

## 🌐 Application Access URLs

| Application | URL | Description |
|-------------|-----|-------------|
| **Main System** | http://localhost:8501 | Complete orchestrated system with all components |
| **Enhanced Dashboard** | http://localhost:8502 | Database analytics and monitoring |
| **Maneuvering System** | http://localhost:8503 | Visual maneuver planning and execution |
| **Basic UI** | http://localhost:8504 | Original satellite tracking interface |

## 🗄️ Database Configuration

### Connection Details
- **Host:** localhost
- **Port:** 5432  
- **Database:** orbital_ballet
- **Username:** postgres
- **Password:** postgres

### Database URL
```bash
export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/orbital_ballet'
```

### Database Management
```bash
# Connect to database
docker-compose exec database psql -U postgres -d orbital_ballet

# View tables
\dt

# Reset database
docker-compose run --rm db-init

# Backup database
docker-compose exec database pg_dump -U postgres orbital_ballet > backup.sql
```

## 🔧 System Management

### Docker Commands
```bash
# Start system
docker-compose up -d

# Stop system  
docker-compose down

# Restart specific service
docker-compose restart app-main

# View service logs
docker-compose logs -f app-main

# Scale service (if needed)
docker-compose up -d --scale app-main=2

# Remove everything
docker-compose down -v --remove-orphans
```

### Local Development Commands
```bash
# Activate environment
source venv/bin/activate

# Update dependencies
pip install -r requirements.txt --upgrade

# Run tests (if available)
pytest

# Database operations
python setup_database.py --help
```

## 📊 System Monitoring

### Health Checks
- **Application Health:** `curl http://localhost:8501/_stcore/health`
- **Database Health:** `docker-compose exec database pg_isready -U postgres`
- **System Status:** `docker-compose ps`

### Log Locations
- **Docker Logs:** `docker-compose logs [service]`
- **Application Logs:** `./logs/` directory
- **Database Logs:** Docker container logs

### Performance Monitoring
- Monitor CPU/Memory usage: `docker stats`
- Database connections: Check via database dashboard
- Application metrics: Built into each UI

## 🚨 Troubleshooting

### Common Issues

#### Database Connection Failed
```bash
# Check if database is running
docker-compose ps database

# Restart database
docker-compose restart database

# Check database logs
docker-compose logs database
```

#### Port Already in Use
```bash
# Find process using port
lsof -i :8501

# Kill process
kill -9 <PID>

# Or use different port
streamlit run app.py --server.port 8505
```

#### Dependencies Issues
```bash
# Rebuild Docker images
docker-compose build --no-cache

# Or reinstall locally
pip install -r requirements.txt --force-reinstall
```

#### Permission Errors
```bash
# Fix script permissions
chmod +x start_full_system.sh start_local.sh

# Fix Docker permissions (Linux)
sudo usermod -aG docker $USER
```

### Debug Mode

#### Enable Debug Logging
```bash
# Set environment variable
export STREAMLIT_LOGGER_LEVEL=debug

# Or in Docker Compose
environment:
  - STREAMLIT_LOGGER_LEVEL=debug
```

#### Development Mode
```bash
# Run with auto-reload
streamlit run app.py --server.runOnSave true

# Debug database
python setup_database.py --verbose
```

## 🔐 Security Configuration

### Production Environment Variables
```bash
export DATABASE_URL='postgresql://user:pass@host:5432/db'
export STREAMLIT_SERVER_ENABLE_CORS=false
export STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=true
```

### Firewall Rules
```bash
# Allow only necessary ports
ufw allow 8501:8504/tcp
ufw allow 5432/tcp  # Database (internal only)
```

## 📈 Performance Optimization

### Resource Requirements

| Component | RAM | CPU | Storage |
|-----------|-----|-----|---------|
| Database | 2GB | 1 core | 10GB |
| Main App | 4GB | 2 cores | 1GB |
| Enhanced | 2GB | 1 core | 500MB |
| Maneuvering | 3GB | 1 core | 500MB |
| **Total** | **11GB** | **5 cores** | **12GB** |

### Optimization Tips
- Use SSD storage for database
- Enable database connection pooling
- Configure appropriate memory limits
- Use Redis for caching (future enhancement)

## 🚀 Quick Start Summary

### For Immediate Testing (Docker)
```bash
./start_full_system.sh
# Wait 2-3 minutes for full startup
# Access: http://localhost:8501
```

### For Development (Local)
```bash
./start_local.sh
# Choose option 1 for main system
# Access: http://localhost:8501
```

### For Production (Cloud)
```bash
# Copy all files to server
scp -r . user@server:/opt/orbital-ballet/

# On server
cd /opt/orbital-ballet
./start_full_system.sh

# Configure reverse proxy (nginx/apache)
# Set up SSL certificates
# Configure monitoring
```

---

## 🎯 Recommended Approach

**For first-time users:** Use Docker deployment with `./start_full_system.sh`

**For developers:** Use local development with `./start_local.sh`

**For production:** Use Docker with custom environment variables and reverse proxy

Your complete Live Orbital Ballet system is now ready to run with full backend integration! 🛰️✨