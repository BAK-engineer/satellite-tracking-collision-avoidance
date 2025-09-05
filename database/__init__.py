"""
Live Orbital Ballet - Database Module
Comprehensive database layer for satellite tracking system
"""

from .connection import (
    DatabaseManager,
    db_manager,
    get_db_session,
    init_database,
    close_database,
    database_health_check,
    DatabaseUtils
)

from .models import (
    Base,
    TLEData,
    Satellite,
    DebrisObject,
    OrbitalState,
    RiskAssessment,
    CollisionPrediction,
    ManeuverPlan,
    SystemLog,
    UserSession
)

from .dao import (
    TLEDataDAO,
    SatelliteDAO,
    OrbitalStateDAO,
    RiskAssessmentDAO,
    CollisionPredictionDAO,
    ManeuverPlanDAO,
    SystemLogDAO,
    AnalyticsDAO,
    log_info,
    log_warning,
    log_error,
    log_critical
)

__version__ = "1.0.0"
__all__ = [
    # Connection management
    'DatabaseManager',
    'db_manager',
    'get_db_session',
    'init_database',
    'close_database',
    'database_health_check',
    'DatabaseUtils',
    
    # Models
    'Base',
    'TLEData',
    'Satellite',
    'DebrisObject',
    'OrbitalState',
    'RiskAssessment',
    'CollisionPrediction',
    'ManeuverPlan',
    'SystemLog',
    'UserSession',
    
    # Data Access Objects
    'TLEDataDAO',
    'SatelliteDAO',
    'OrbitalStateDAO',
    'RiskAssessmentDAO',
    'CollisionPredictionDAO',
    'ManeuverPlanDAO',
    'SystemLogDAO',
    'AnalyticsDAO',
    
    # Logging functions
    'log_info',
    'log_warning',
    'log_error',
    'log_critical'
]

# Module initialization
def setup_database(database_url=None, create_tables=True, echo=False):
    """
    Initialize the database system
    
    Args:
        database_url: PostgreSQL connection URL
        create_tables: Whether to create database tables
        echo: Whether to echo SQL statements
        
    Returns:
        bool: True if initialization successful
    """
    return init_database(database_url, create_tables, echo)

def get_system_status():
    """Get comprehensive system status"""
    health = database_health_check()
    stats = AnalyticsDAO.get_system_statistics()
    
    return {
        'database_health': health,
        'system_statistics': stats,
        'version': __version__
    }