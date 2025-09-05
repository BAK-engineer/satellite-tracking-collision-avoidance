"""
Live Orbital Ballet - Database Setup and Initialization Script
Handles database creation, initialization, and sample data loading
"""

import os
import sys
import argparse
import logging
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
import json

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('database_setup.log')
    ]
)
logger = logging.getLogger(__name__)

def check_dependencies():
    """Check if all required dependencies are installed"""
    required_packages = ['sqlalchemy', 'psycopg2', 'alembic']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        logger.error(f"Missing required packages: {missing_packages}")
        logger.info("Install with: pip install -r requirements.txt")
        return False
    
    return True

def setup_database(database_url: Optional[str] = None, 
                  create_tables: bool = True,
                  load_sample_data: bool = False,
                  reset_database: bool = False) -> bool:
    """
    Setup and initialize the orbital ballet database
    
    Args:
        database_url: PostgreSQL connection URL
        create_tables: Whether to create database tables
        load_sample_data: Whether to load sample data
        reset_database: Whether to reset existing database
        
    Returns:
        True if setup successful, False otherwise
    """
    
    try:
        # Import database modules
        from database import (
            init_database, close_database, database_health_check,
            DatabaseUtils, db_manager
        )
        
        logger.info("🚀 Starting Live Orbital Ballet database setup...")
        
        # Initialize database connection
        logger.info("📡 Connecting to database...")
        success = init_database(database_url=database_url, create_tables=False, echo=False)
        
        if not success:
            logger.error("❌ Failed to connect to database")
            return False
        
        logger.info("✅ Database connection established")
        
        # Check database health
        health = database_health_check()
        if health['status'] != 'healthy':
            logger.error(f"❌ Database health check failed: {health}")
            return False
        
        logger.info("✅ Database health check passed")
        
        # Reset database if requested
        if reset_database:
            logger.warning("⚠️ Resetting database (this will delete all data)...")
            confirmation = input("Are you sure you want to reset the database? (yes/no): ")
            
            if confirmation.lower() == 'yes':
                success = db_manager.drop_tables()
                if success:
                    logger.info("✅ Database tables dropped")
                else:
                    logger.error("❌ Failed to drop tables")
                    return False
            else:
                logger.info("Database reset cancelled")
                return False
        
        # Create tables if requested
        if create_tables:
            logger.info("🏗️ Creating database tables...")
            success = db_manager.create_tables()
            
            if success:
                logger.info("✅ Database tables created successfully")
            else:
                logger.error("❌ Failed to create database tables")
                return False
        
        # Load sample data if requested
        if load_sample_data:
            logger.info("📊 Loading sample data...")
            success = load_sample_data_func()
            
            if success:
                logger.info("✅ Sample data loaded successfully")
            else:
                logger.error("❌ Failed to load sample data")
                return False
        
        # Get final statistics
        stats = DatabaseUtils.get_table_stats()
        logger.info("📈 Database setup completed successfully!")
        logger.info("📊 Table statistics:")
        for table, count in stats.items():
            logger.info(f"  {table}: {count} records")
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Database module import failed: {e}")
        logger.info("Make sure to install database dependencies: pip install -r requirements.txt")
        return False
        
    except Exception as e:
        logger.error(f"❌ Database setup failed: {e}")
        return False
    
    finally:
        try:
            close_database()
            logger.info("🔌 Database connection closed")
        except:
            pass

def load_sample_data_func() -> bool:
    """Load sample data for testing and demonstration"""
    
    try:
        from database import (
            get_db_session, TLEDataDAO, SatelliteDAO, OrbitalStateDAO,
            RiskAssessmentDAO, CollisionPredictionDAO, log_info
        )
        from decimal import Decimal
        import uuid
        
        # Sample TLE data for ISS and a few other satellites
        sample_tle_data = [
            {
                'norad_id': 25544,
                'satellite_name': 'ISS (ZARYA)',
                'line1': '1 25544U 98067A   23350.86206018  .00008262  00000+0  15265-3 0  9990',
                'line2': '2 25544  51.6429 315.3769 0005172  85.7426 274.4929 15.48919103428996',
                'classification': 'U',
                'launch_year': 1998,
                'launch_number': 67,
                'piece_designator': 'A',
                'is_active': True,
                'data_source': 'SAMPLE'
            },
            {
                'norad_id': 20580,
                'satellite_name': 'HUBBLE SPACE TELESCOPE',
                'line1': '1 20580U 90037B   23350.12345678  .00001234  00000+0  12345-4 0  9999',
                'line2': '2 20580  28.4687  45.1234 0002345 123.4567 236.5432 15.12345678123456',
                'classification': 'U',
                'launch_year': 1990,
                'launch_number': 37,
                'piece_designator': 'B',
                'is_active': True,
                'data_source': 'SAMPLE'
            },
            {
                'norad_id': 43013,
                'satellite_name': 'STARLINK-1007',
                'line1': '1 43013U 17083A   23350.54321098  .00005678  00000+0  56789-4 0  9998',
                'line2': '2 43013  53.0123 123.4567 0001234 234.5678 125.4321 15.23456789234567',
                'classification': 'U',
                'launch_year': 2017,
                'launch_number': 83,
                'piece_designator': 'A',
                'is_active': True,
                'data_source': 'SAMPLE'
            }
        ]
        
        # Create TLE records and satellites
        satellite_ids = {}
        
        for tle_data in sample_tle_data:
            # Create TLE record
            tle_record = TLEDataDAO.create_or_update_tle(tle_data)
            
            if tle_record:
                logger.info(f"✅ Created TLE for {tle_record.satellite_name}")
                
                # Create satellite record
                satellite_data = {
                    'norad_id': tle_data['norad_id'],
                    'name': tle_data['satellite_name'],
                    'satellite_type': _determine_satellite_type(tle_data['satellite_name']),
                    'operational_status': 'ACTIVE',
                    'track_continuously': True,
                    'collision_monitoring': True,
                    'priority_level': 8 if 'ISS' in tle_data['satellite_name'] else 5,
                    'country_code': 'USA' if 'ISS' not in tle_data['satellite_name'] else 'INT'
                }
                
                satellite = SatelliteDAO.create_satellite(satellite_data)
                
                if satellite:
                    logger.info(f"✅ Created satellite record for {satellite.name}")
                    satellite_ids[tle_data['norad_id']] = satellite.id
                    
                    # Create some sample orbital states
                    _create_sample_orbital_states(satellite, tle_data['norad_id'])
        
        # Create sample risk assessments and collision predictions
        if len(satellite_ids) >= 2:
            _create_sample_risk_assessments(list(satellite_ids.values()))
        
        # Log sample data creation
        log_info('SETUP', 'Sample data loaded successfully', category='INITIALIZATION')
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to load sample data: {e}")
        return False

def _determine_satellite_type(satellite_name: str) -> str:
    """Determine satellite type from name"""
    name_upper = satellite_name.upper()
    
    if 'ISS' in name_upper or 'STATION' in name_upper:
        return 'scientific'
    elif 'HUBBLE' in name_upper or 'TELESCOPE' in name_upper:
        return 'scientific'
    elif 'STARLINK' in name_upper or 'IRIDIUM' in name_upper:
        return 'communication'
    elif 'GPS' in name_upper or 'GLONASS' in name_upper:
        return 'navigation'
    elif 'WEATHER' in name_upper or 'NOAA' in name_upper:
        return 'weather'
    else:
        return 'commercial'

def _create_sample_orbital_states(satellite, norad_id: int):
    """Create sample orbital states for a satellite"""
    from database import OrbitalStateDAO
    from decimal import Decimal
    import numpy as np
    
    current_time = datetime.now(timezone.utc)
    
    # Create states for the last 2 hours (every 10 minutes)
    for i in range(12):
        time_offset = timedelta(minutes=i * 10)
        epoch = current_time - time_offset
        
        # Simulate orbital position (simplified)
        altitude = 400 + np.random.uniform(-20, 50)  # km
        theta = (i * 15) * np.pi / 180  # Degrees to radians
        
        r = 6371 + altitude  # Earth radius + altitude
        x = r * np.cos(theta)
        y = r * np.sin(theta)
        z = r * 0.1 * np.sin(theta * 2)  # Small z variation
        
        # Orbital velocity (simplified)
        v = np.sqrt(398600.4418 / r)  # Circular orbital velocity
        vx = -v * np.sin(theta)
        vy = v * np.cos(theta)
        vz = 0.1 * np.cos(theta * 2)
        
        state_data = {
            'object_type': 'SATELLITE',
            'object_id': satellite.id,
            'norad_id': norad_id,
            'position_x': Decimal(str(x)),
            'position_y': Decimal(str(y)),
            'position_z': Decimal(str(z)),
            'velocity_x': Decimal(str(vx)),
            'velocity_y': Decimal(str(vy)),
            'velocity_z': Decimal(str(vz)),
            'altitude_km': Decimal(str(altitude)),
            'epoch': epoch,
            'prediction_type': 'SGP4'
        }
        
        OrbitalStateDAO.save_orbital_state(state_data)

def _create_sample_risk_assessments(satellite_ids: list):
    """Create sample risk assessments between satellites"""
    from database import RiskAssessmentDAO, CollisionPredictionDAO
    from decimal import Decimal
    import uuid
    
    if len(satellite_ids) < 2:
        return
    
    # Create a risk assessment between first two satellites
    primary_id = satellite_ids[0]
    secondary_id = satellite_ids[1]
    
    risk_data = {
        'primary_object_type': 'SATELLITE',
        'primary_object_id': primary_id,
        'secondary_object_type': 'SATELLITE',
        'secondary_object_id': secondary_id,
        'collision_probability': Decimal('0.001'),  # 0.1%
        'miss_distance_km': Decimal('2.5'),
        'time_to_closest_approach': datetime.now(timezone.utc) + timedelta(hours=3),
        'physics_risk_score': Decimal('0.15'),
        'ml_risk_score': Decimal('0.12'),
        'hybrid_risk_score': Decimal('0.13'),
        'risk_category': 'MEDIUM',
        'confidence_level': Decimal('0.85'),
        'assessment_method': 'HYBRID_AI'
    }
    
    risk_assessment = RiskAssessmentDAO.create_risk_assessment(risk_data)
    
    if risk_assessment:
        logger.info("✅ Created sample risk assessment")
        
        # Create collision prediction
        prediction_data = {
            'risk_assessment_id': risk_assessment.id,
            'predicted_collision_time': datetime.now(timezone.utc) + timedelta(hours=3, minutes=15),
            'collision_probability': Decimal('0.001'),
            'miss_distance_km': Decimal('2.5'),
            'relative_velocity_kms': Decimal('14.2'),
            'confidence_level': Decimal('0.85')
        }
        
        prediction = CollisionPredictionDAO.create_collision_prediction(prediction_data)
        
        if prediction:
            logger.info("✅ Created sample collision prediction")

def print_connection_examples():
    """Print database connection examples for different environments"""
    
    print("\n" + "="*60)
    print("DATABASE CONNECTION EXAMPLES")
    print("="*60)
    
    examples = {
        "Local PostgreSQL": "postgresql://postgres:password@localhost:5432/orbital_ballet",
        "Docker PostgreSQL": "postgresql://postgres:postgres@localhost:5432/orbital_ballet",
        "Heroku Postgres": "postgresql://user:pass@host:5432/dbname",
        "AWS RDS": "postgresql://username:password@rds-endpoint:5432/orbital_ballet",
        "Google Cloud SQL": "postgresql://user:pass@google-sql-ip:5432/orbital_ballet"
    }
    
    print("\n📋 Connection URL Examples:")
    for name, url in examples.items():
        print(f"  {name}:")
        print(f"    {url}")
        print()
    
    print("🔧 Environment Variable Setup:")
    print("  export DATABASE_URL='postgresql://user:pass@host:5432/dbname'")
    print("  # or")
    print("  export DB_HOST=localhost")
    print("  export DB_PORT=5432")
    print("  export DB_NAME=orbital_ballet")
    print("  export DB_USER=postgres")
    print("  export DB_PASSWORD=your_password")
    print()
    
    print("🐳 Quick Docker PostgreSQL Setup:")
    print("  docker run --name orbital-postgres \\")
    print("    -e POSTGRES_DB=orbital_ballet \\")
    print("    -e POSTGRES_USER=postgres \\")
    print("    -e POSTGRES_PASSWORD=postgres \\")
    print("    -p 5432:5432 -d postgres:13")
    print()

def main():
    """Main setup script"""
    
    parser = argparse.ArgumentParser(description='Live Orbital Ballet Database Setup')
    parser.add_argument('--url', help='Database connection URL')
    parser.add_argument('--create-tables', action='store_true', help='Create database tables')
    parser.add_argument('--sample-data', action='store_true', help='Load sample data')
    parser.add_argument('--reset', action='store_true', help='Reset database (WARNING: deletes all data)')
    parser.add_argument('--check-deps', action='store_true', help='Check dependencies only')
    parser.add_argument('--examples', action='store_true', help='Show connection examples')
    
    args = parser.parse_args()
    
    print("🌍 Live Orbital Ballet - Database Setup")
    print("=" * 50)
    
    # Show examples
    if args.examples:
        print_connection_examples()
        return
    
    # Check dependencies
    if args.check_deps:
        if check_dependencies():
            print("✅ All dependencies are installed")
        else:
            print("❌ Missing dependencies")
            sys.exit(1)
        return
    
    # Check dependencies before proceeding
    if not check_dependencies():
        print("❌ Missing dependencies. Use --examples for setup help.")
        sys.exit(1)
    
    # Get database URL
    database_url = args.url or os.getenv('DATABASE_URL')
    
    if not database_url:
        print("\n⚠️  No database URL provided.")
        print("Use --url parameter or set DATABASE_URL environment variable.")
        print("Use --examples to see connection examples.")
        sys.exit(1)
    
    # Confirm reset if requested
    if args.reset:
        print("⚠️  WARNING: This will delete ALL existing data!")
        confirmation = input("Continue with database reset? (yes/no): ")
        if confirmation.lower() != 'yes':
            print("Database reset cancelled.")
            sys.exit(0)
    
    # Run setup
    success = setup_database(
        database_url=database_url,
        create_tables=args.create_tables,
        load_sample_data=args.sample_data,
        reset_database=args.reset
    )
    
    if success:
        print("\n🎉 Database setup completed successfully!")
        print("\n📋 Next steps:")
        print("  1. Run the enhanced application: streamlit run ui_enhanced.py")
        print("  2. Or test database integration: python database_integration_example.py")
        print("  3. View application at: http://localhost:8501")
        
        if args.sample_data:
            print("\n📊 Sample data loaded - you can explore the features immediately!")
    else:
        print("\n❌ Database setup failed. Check logs above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()