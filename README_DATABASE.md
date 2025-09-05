# Live Orbital Ballet - Enhanced with Database Integration

🌍 **Live Orbital Ballet** is now enhanced with comprehensive database integration, providing persistent data storage, historical analysis, and advanced analytics for satellite tracking and collision risk assessment.

## 🚀 What's New in the Enhanced Version

### ✨ Key Features Added

1. **🗄️ Persistent Data Storage**
   - PostgreSQL database with comprehensive schema
   - Historical satellite position tracking
   - Risk assessment storage and trends
   - System logs and audit trails

2. **📊 Advanced Analytics**
   - Collision risk trend analysis
   - System performance monitoring  
   - Database health checks
   - Real-time statistics dashboard

3. **🔄 Backward Compatibility**
   - Original functionality preserved
   - Graceful fallback to memory-only mode
   - Seamless integration with existing code

4. **🛡️ Enhanced Risk Management**
   - Persistent risk assessments
   - Collision prediction history
   - Maneuver planning and tracking
   - AI-powered risk scoring

## 📁 New File Structure

```
📦 Live Orbital Ballet Enhanced
├── 🗄️ Database System
│   ├── database/
│   │   ├── __init__.py           # Database module exports
│   │   ├── models.py             # SQLAlchemy ORM models
│   │   ├── connection.py         # Database connection manager
│   │   └── dao.py               # Data Access Objects
│   ├── database_schema.sql       # PostgreSQL schema
│   └── setup_database.py         # Database setup script
│
├── 🔄 Enhanced Modules  
│   ├── data_enhanced.py          # Enhanced data manager
│   ├── ui_enhanced.py           # Enhanced UI with database features
│   └── database_integration_example.py  # Integration guide
│
├── 📖 Original Files (Preserved)
│   ├── data.py                  # Original data manager
│   ├── ui.py                   # Original UI
│   └── orbital_mechanics.py    # Orbital calculations
│
└── 📋 Configuration
    ├── requirements.txt         # Updated dependencies
    └── README_DATABASE.md      # This file
```

## 🛠️ Quick Setup Guide

### 1. Install Dependencies

```bash
# Install all dependencies including database support
pip install -r requirements.txt

# Or install database dependencies separately
pip install sqlalchemy==2.0.25 psycopg2-binary==2.9.9 alembic==1.13.1
```

### 2. Setup Database (Optional)

#### Option A: Quick Docker Setup
```bash
# Start PostgreSQL in Docker
docker run --name orbital-postgres \
  -e POSTGRES_DB=orbital_ballet \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 -d postgres:13

# Set environment variable
export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/orbital_ballet'
```

#### Option B: Use Existing PostgreSQL
```bash
# Set your database connection
export DATABASE_URL='postgresql://user:password@host:5432/database_name'

# Or set individual components
export DB_HOST=your_host
export DB_PORT=5432
export DB_NAME=orbital_ballet
export DB_USER=your_user
export DB_PASSWORD=your_password
```

### 3. Initialize Database

```bash
# Check dependencies
python setup_database.py --check-deps

# Create tables and load sample data
python setup_database.py --create-tables --sample-data

# View connection examples
python setup_database.py --examples
```

### 4. Run Enhanced Application

```bash
# Run the enhanced UI (with database features)
streamlit run ui_enhanced.py

# Or run the original UI (memory-only)
streamlit run ui.py
```

## 🎯 Usage Examples

### Enhanced Data Manager

```python
from data_enhanced import EnhancedDataManager

# Initialize with database support
data_manager = EnhancedDataManager(use_database=True)

# Fetch and store satellite data
satellites = data_manager.get_satellite_data(limit=50, force_refresh=True)

# Get enhanced status with database metrics
status = data_manager.get_status_info()
print(f"Database enabled: {status['database_enabled']}")
print(f"Satellites in DB: {status.get('database_statistics', {}).get('satellites_total', 0)}")
```

### Database Operations

```python
from database import TLEDataDAO, SatelliteDAO, get_system_status

# Get satellites from database
satellites = SatelliteDAO.get_tracked_satellites()

# Get system status
status = get_system_status()
print(f"Database health: {status['database_health']['status']}")
```

### Direct Database Setup

```python
from database import init_database, setup_database

# Initialize database with tables
success = init_database(create_tables=True)

if success:
    print("✅ Database ready!")
else:
    print("❌ Database setup failed")
```

## 🏗️ Database Schema Overview

The system includes 12 interconnected tables:

### Core Tables
- **`tle_data`** - Two-Line Element data from Celestrak
- **`satellites`** - Satellite metadata and tracking preferences
- **`debris_objects`** - Space debris tracking
- **`orbital_states`** - Position/velocity history

### Analysis Tables
- **`risk_assessments`** - AI-powered collision risk analysis
- **`collision_predictions`** - Predicted collision events
- **`maneuver_plans`** - Collision avoidance maneuvers

### System Tables
- **`system_logs`** - Comprehensive audit trails
- **`user_sessions`** - Dashboard usage tracking

## 🔄 Migration from Original Version

The enhanced version maintains **100% backward compatibility**:

### Automatic Fallback
- If database is unavailable → automatically uses memory-only mode
- Original `data.py` and `ui.py` continue to work unchanged
- Enhanced modules (`data_enhanced.py`, `ui_enhanced.py`) provide additional features

### Migration Strategies

#### Strategy 1: Gradual Migration
```python
# Keep using original modules, add database features gradually
from data import DataManager  # Original
from database import init_database  # Add database

# Initialize database
init_database(create_tables=True)

# Your existing code continues to work
data_manager = DataManager()
```

#### Strategy 2: Full Enhanced Mode
```python
# Use enhanced modules for full database integration
from data_enhanced import EnhancedDataManager
from ui_enhanced import main

# Enhanced functionality with database persistence
data_manager = EnhancedDataManager(use_database=True)
```

## 📊 Enhanced Features

### 1. Database Dashboard
- Real-time system statistics
- Database health monitoring
- Recent activity logs
- Error tracking and alerts

### 2. Analytics & Reporting
- Collision risk trends over time
- Satellite tracking statistics
- Risk assessment distribution
- System performance metrics

### 3. Historical Analysis
- Orbital trajectory reconstruction
- Risk assessment history
- Collision prediction accuracy tracking
- Maneuver effectiveness analysis

### 4. Advanced Visualization
- Historical orbital paths
- Risk zone visualization  
- Collision prediction timelines
- Database-backed real-time updates

## 🔧 Configuration Options

### Environment Variables
```bash
# Database connection (primary method)
DATABASE_URL='postgresql://user:pass@host:5432/dbname'

# Alternative: individual components
DB_HOST=localhost
DB_PORT=5432
DB_NAME=orbital_ballet
DB_USER=postgres
DB_PASSWORD=your_password

# Optional: disable database features
DISABLE_DATABASE=true
```

### Code Configuration
```python
# Explicit database control
data_manager = EnhancedDataManager(use_database=True)   # Force enable
data_manager = EnhancedDataManager(use_database=False)  # Force disable
data_manager = EnhancedDataManager()                    # Auto-detect
```

## 🚨 Troubleshooting

### Common Issues

#### 1. Database Connection Failed
```bash
# Check dependencies
python setup_database.py --check-deps

# Verify connection
python -c "import psycopg2; print('✅ PostgreSQL driver OK')"

# Test connection
python setup_database.py --examples
```

#### 2. Import Errors
```bash
# Install missing dependencies
pip install -r requirements.txt

# Verify modules
python -c "from database import init_database; print('✅ Database module OK')"
python -c "from data_enhanced import EnhancedDataManager; print('✅ Enhanced data OK')"
```

#### 3. Permission Issues
```bash
# Check PostgreSQL permissions
psql -h localhost -U postgres -d orbital_ballet -c "SELECT version();"

# Verify user has create/write permissions
```

### Fallback to Memory Mode
If database setup fails, the system automatically falls back to memory-only mode:

```bash
# Run without database
streamlit run ui.py  # Original UI

# Or enhanced UI in memory-only mode
DISABLE_DATABASE=true streamlit run ui_enhanced.py
```

## 🎯 Next Steps

### Immediate Actions
1. **Install dependencies**: `pip install -r requirements.txt`
2. **Setup database**: Follow Quick Setup Guide above
3. **Run enhanced app**: `streamlit run ui_enhanced.py`
4. **Explore features**: Check database dashboard and analytics

### Advanced Usage
1. **Custom risk models**: Extend `RiskAssessment` table
2. **Additional data sources**: Add more TLE providers  
3. **Real-time updates**: Implement WebSocket connections
4. **Machine learning**: Train custom collision prediction models

### Production Deployment
1. **Database optimization**: Add indexes and partitioning
2. **Monitoring**: Set up Prometheus/Grafana monitoring
3. **Backup strategy**: Implement automated backups
4. **Load balancing**: Scale horizontally with multiple instances

## 📚 API Reference

### Database Module
- `init_database()` - Initialize database connection
- `get_system_status()` - Get comprehensive system status
- `DatabaseUtils.get_table_stats()` - Get table statistics

### Enhanced Data Manager
- `get_satellite_data(force_refresh=True)` - Fetch with database storage
- `store_orbital_states()` - Persist orbital calculations  
- `get_status_info()` - Enhanced status with database metrics

### Data Access Objects (DAOs)
- `TLEDataDAO` - TLE data operations
- `SatelliteDAO` - Satellite management
- `OrbitalStateDAO` - Position/velocity storage
- `RiskAssessmentDAO` - Risk analysis operations

## 🤝 Contributing

The enhanced database system is designed to be:
- **Modular**: Each component can be used independently
- **Extensible**: Easy to add new features and data sources
- **Backward compatible**: Existing code continues to work
- **Well documented**: Comprehensive inline documentation

Feel free to contribute by:
1. Adding new data sources or analysis algorithms
2. Improving database schema or performance
3. Enhancing visualizations or dashboard features
4. Adding tests or documentation improvements

---

🌟 **Live Orbital Ballet Enhanced** - Bringing persistent data storage and advanced analytics to satellite tracking and collision risk assessment!