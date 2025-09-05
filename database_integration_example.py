"""
Live Orbital Ballet - Database Integration Example
Demonstrates how to integrate the database system with the existing application
"""

import os
from datetime import datetime, timezone
from decimal import Decimal
import uuid

# Import our database module
from database import (
    init_database, close_database, get_system_status,
    TLEDataDAO, SatelliteDAO, OrbitalStateDAO, RiskAssessmentDAO,
    log_info, log_error
)

def example_database_integration():
    """Example of integrating database with the satellite tracking application"""
    
    # 1. Initialize database
    print("Initializing database...")
    db_url = "postgresql://postgres:postgres@localhost:5432/orbital_ballet"
    
    # In production, you might read this from environment variables:
    # db_url = os.getenv('DATABASE_URL')
    
    success = init_database(database_url=db_url, create_tables=True, echo=False)
    
    if not success:
        print("❌ Failed to initialize database")
        return False
    
    print("✅ Database initialized successfully")
    
    # 2. Get system status
    status = get_system_status()
    print(f"Database health: {status['database_health']['status']}")
    print(f"System statistics: {status['system_statistics']}")
    
    # 3. Example: Store TLE data (integrating with existing data.py)
    print("\n📡 Storing TLE data...")
    
    # Sample TLE data (normally this would come from your existing data.py module)
    sample_tle = {
        'norad_id': 25544,  # ISS
        'satellite_name': 'ISS (ZARYA)',
        'line1': '1 25544U 98067A   23350.86206018  .00008262  00000+0  15265-3 0  9990',
        'line2': '2 25544  51.6429 315.3769 0005172  85.7426 274.4929 15.48919103428996',
        'classification': 'U',
        'launch_year': 1998,
        'launch_number': 67,
        'piece_designator': 'A',
        'is_active': True,
        'data_source': 'CELESTRAK'
    }
    
    tle_record = TLEDataDAO.create_or_update_tle(sample_tle)
    if tle_record:
        print(f"✅ TLE stored for NORAD ID: {tle_record.norad_id}")
        log_info('DATA_IMPORT', f'TLE data stored for {tle_record.satellite_name}', 
                object_type='SATELLITE', object_id=tle_record.id)
    else:
        print("❌ Failed to store TLE data")
        return False
    
    # 4. Example: Create satellite record
    print("\n🛰️ Creating satellite record...")
    
    satellite_data = {
        'norad_id': 25544,
        'name': 'International Space Station',
        'country_code': 'INT',
        'satellite_type': 'scientific',
        'operational_status': 'ACTIVE',
        'mass_kg': Decimal('420000.0'),  # ISS mass in kg
        'orbital_regime': 'LEO',
        'mission_description': 'International Space Station - Low Earth Orbit Laboratory',
        'owner_operator': 'International',
        'priority_level': 10,
        'track_continuously': True,
        'collision_monitoring': True
    }
    
    satellite = SatelliteDAO.create_satellite(satellite_data)
    if satellite:
        print(f"✅ Satellite created: {satellite.name}")
        log_info('SATELLITE_MGMT', f'Satellite record created for {satellite.name}',
                object_type='SATELLITE', object_id=satellite.id)
    else:
        print("❌ Failed to create satellite record")
        return False
    
    # 5. Example: Store orbital state (integrating with existing orbital calculations)
    print("\n🌍 Storing orbital state...")
    
    # Sample orbital state data (normally computed by SGP4 in your existing code)
    state_data = {
        'object_type': 'SATELLITE',
        'object_id': satellite.id,
        'norad_id': 25544,
        'position_x': Decimal('6800.123'),   # km
        'position_y': Decimal('-1234.567'),  # km
        'position_z': Decimal('2345.789'),   # km
        'velocity_x': Decimal('1.234'),      # km/s
        'velocity_y': Decimal('7.456'),      # km/s
        'velocity_z': Decimal('-0.789'),     # km/s
        'altitude_km': Decimal('408.5'),
        'orbital_period_sec': Decimal('5574.2'),
        'epoch': datetime.now(timezone.utc),
        'prediction_type': 'SGP4',
        'accuracy_estimate_km': Decimal('0.5')
    }
    
    orbital_state = OrbitalStateDAO.save_orbital_state(state_data)
    if orbital_state:
        print(f"✅ Orbital state stored for altitude: {orbital_state.altitude_km} km")
        log_info('ORBITAL_TRACKING', f'Orbital state computed for NORAD {orbital_state.norad_id}',
                object_type='SATELLITE', object_id=orbital_state.object_id)
    else:
        print("❌ Failed to store orbital state")
        return False
    
    # 6. Example: Retrieve and display data
    print("\n📊 Retrieving stored data...")
    
    # Get active satellites
    tracked_satellites = SatelliteDAO.get_tracked_satellites()
    print(f"Active tracked satellites: {len(tracked_satellites)}")
    
    for sat in tracked_satellites:
        print(f"  - {sat.name} (NORAD {sat.norad_id}) - Priority {sat.priority_level}")
    
    # Get current positions
    current_positions = OrbitalStateDAO.get_current_positions(limit=10)
    print(f"Current position records: {len(current_positions)}")
    
    for pos in current_positions:
        print(f"  - NORAD {pos['norad_id']}: Altitude {pos['altitude_km']:.1f} km")
    
    # 7. Example: Create a risk assessment
    print("\n⚠️ Creating risk assessment...")
    
    # Create a dummy debris object first
    from database.dao import DebrisObject
    with database.get_db_session() as session:
        debris = DebrisObject(
            debris_id='DEBRIS_001',
            debris_type='fragment',
            estimated_size_m=Decimal('0.05'),
            risk_category='MEDIUM'
        )
        session.add(debris)
        session.flush()
        debris_id = debris.id
    
    risk_data = {
        'primary_object_type': 'SATELLITE',
        'primary_object_id': satellite.id,
        'secondary_object_type': 'DEBRIS',
        'secondary_object_id': debris_id,
        'collision_probability': Decimal('0.001'),  # 0.1% chance
        'miss_distance_km': Decimal('0.5'),
        'time_to_closest_approach': datetime.now(timezone.utc),
        'physics_risk_score': Decimal('0.15'),
        'ml_risk_score': Decimal('0.12'),
        'hybrid_risk_score': Decimal('0.13'),
        'risk_category': 'MEDIUM',
        'confidence_level': Decimal('0.85'),
        'assessment_method': 'HYBRID_AI'
    }
    
    risk_assessment = RiskAssessmentDAO.create_risk_assessment(risk_data)
    if risk_assessment:
        print(f"✅ Risk assessment created with probability: {risk_assessment.collision_probability}")
        log_info('RISK_ANALYSIS', 'Risk assessment completed',
                object_type='SATELLITE', object_id=satellite.id)
    
    # 8. Get updated system statistics
    print("\n📈 Updated system statistics:")
    final_stats = get_system_status()['system_statistics']
    for key, value in final_stats.items():
        print(f"  {key}: {value}")
    
    print("\n✅ Database integration example completed successfully!")
    return True

def integration_with_existing_app():
    """
    Example showing how to modify existing app code to use database
    This shows the pattern for integrating with data.py and ui.py
    """
    print("\n" + "="*60)
    print("INTEGRATION PATTERN FOR EXISTING APPLICATION")
    print("="*60)
    
    print("""
    To integrate the database with your existing Live Orbital Ballet application:
    
    1. MODIFY data.py:
       - Import: from database import TLEDataDAO, SatelliteDAO, OrbitalStateDAO
       - In fetch_satellite_data(): Store fetched TLEs using TLEDataDAO.create_or_update_tle()
       - In update_orbital_positions(): Store computed positions using OrbitalStateDAO.save_orbital_state()
    
    2. MODIFY ui.py:
       - Import: from database import init_database, get_system_status
       - Add database initialization in main(): init_database(create_tables=True)
       - Add database status to dashboard: status = get_system_status()
       - Replace in-memory data with database queries for persistent storage
    
    3. ENVIRONMENT SETUP:
       - Set DATABASE_URL environment variable
       - Or modify database/connection.py with your PostgreSQL credentials
    
    4. EXAMPLE INTEGRATION CODE:
    """)
    
    example_code = '''
    # In data.py - modify fetch_satellite_data function:
    def fetch_satellite_data():
        """Enhanced version with database storage"""
        satellites = fetch_tle_data()  # existing function
        
        # Store in database
        for sat_data in satellites:
            tle_record = TLEDataDAO.create_or_update_tle({
                'norad_id': sat_data['norad_id'],
                'satellite_name': sat_data['name'],
                'line1': sat_data['line1'],
                'line2': sat_data['line2'],
                'is_active': True,
                'data_source': 'CELESTRAK'
            })
            
            if tle_record:
                # Create/update satellite record
                SatelliteDAO.create_satellite({
                    'norad_id': sat_data['norad_id'],
                    'name': sat_data['name'],
                    'satellite_type': 'communication',  # or determine from data
                    'operational_status': 'ACTIVE',
                    'track_continuously': True
                })
        
        return satellites
    
    # In ui.py - add to main function:
    def main():
        st.set_page_config(...)
        
        # Initialize database
        if 'db_initialized' not in st.session_state:
            success = init_database(create_tables=True)
            st.session_state.db_initialized = success
            
        if not st.session_state.db_initialized:
            st.error("Database connection failed!")
            return
        
        # Add database status to sidebar
        with st.sidebar:
            st.subheader("System Status")
            status = get_system_status()
            st.metric("Database", status['database_health']['status'])
            st.json(status['system_statistics'])
    '''
    
    print(example_code)
    
    print("""
    5. BENEFITS OF DATABASE INTEGRATION:
       - Persistent storage of satellite data and tracking history
       - Historical analysis and trend tracking
       - Risk assessment storage and retrieval
       - System logging and monitoring
       - Multi-user session support
       - Collision prediction history
       - Maneuver planning and execution tracking
    """)

if __name__ == "__main__":
    print("🚀 Live Orbital Ballet - Database Integration Example")
    print("=" * 60)
    
    # Run the integration example
    success = example_database_integration()
    
    if success:
        # Show integration patterns
        integration_with_existing_app()
        
        print("\n" + "="*60)
        print("NEXT STEPS:")
        print("="*60)
        print("""
        1. Set up PostgreSQL database
        2. Configure DATABASE_URL environment variable
        3. Install database dependencies: pip install -r requirements.txt
        4. Modify existing data.py and ui.py files as shown above
        5. Run the application with database persistence!
        """)
    else:
        print("\n❌ Integration example failed. Check database connection.")
    
    # Clean up
    close_database()
    print("\n👋 Database connection closed.")