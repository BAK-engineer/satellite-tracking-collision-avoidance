"""
Live Orbital Ballet - Database Connection Manager
Handles database connections, session management, and initialization
"""

import os
import logging
from contextlib import contextmanager
from typing import Optional, Generator
import urllib.parse

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import NullPool
from sqlalchemy.exc import SQLAlchemyError

from .models import Base

# Configure logging
logger = logging.getLogger(__name__)

class DatabaseManager:
    """Database connection and session manager"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database manager
        
        Args:
            database_url: PostgreSQL connection URL
        """
        self.database_url = database_url or self._get_database_url()
        self.engine = None
        self.SessionLocal = None
        self._initialized = False
    
    def _get_database_url(self) -> str:
        """Get database URL from environment or use default"""
        # Check environment variables
        if 'DATABASE_URL' in os.environ:
            return os.environ['DATABASE_URL']
        
        # Build URL from individual components
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_NAME', 'orbital_ballet')
        username = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', 'postgres')
        
        # URL encode password to handle special characters
        encoded_password = urllib.parse.quote_plus(password)
        
        return f"postgresql://{username}:{encoded_password}@{host}:{port}/{database}"
    
    def initialize(self, create_tables: bool = False, echo: bool = False) -> bool:
        """
        Initialize database connection and engine
        
        Args:
            create_tables: Whether to create database tables
            echo: Whether to echo SQL statements
            
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            # Create engine
            self.engine = create_engine(
                self.database_url,
                echo=echo,
                poolclass=NullPool,  # Disable connection pooling for development
                connect_args={
                    "sslmode": "prefer",
                    "connect_timeout": 10,
                }
            )
            
            # Test connection
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                logger.info("Database connection established successfully")
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Create tables if requested
            if create_tables:
                self.create_tables()
            
            self._initialized = True
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            self.engine = None
            self.SessionLocal = None
            return False
    
    def create_tables(self) -> bool:
        """
        Create all database tables
        
        Returns:
            True if tables created successfully, False otherwise
        """
        if not self.engine:
            logger.error("Database engine not initialized")
            return False
        
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            return False
    
    def drop_tables(self) -> bool:
        """
        Drop all database tables (use with caution!)
        
        Returns:
            True if tables dropped successfully, False otherwise
        """
        if not self.engine:
            logger.error("Database engine not initialized")
            return False
        
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to drop tables: {e}")
            return False
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        Context manager for database sessions
        
        Yields:
            Database session
        """
        if not self._initialized or not self.SessionLocal:
            raise RuntimeError("Database manager not initialized")
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_new_session(self) -> Optional[Session]:
        """
        Get a new database session (caller responsible for closing)
        
        Returns:
            Database session or None if not initialized
        """
        if not self._initialized or not self.SessionLocal:
            return None
        return self.SessionLocal()
    
    def close(self):
        """Close database engine"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.SessionLocal = None
            self._initialized = False
            logger.info("Database connection closed")
    
    def health_check(self) -> dict:
        """
        Perform database health check
        
        Returns:
            Health check results
        """
        result = {
            'status': 'unhealthy',
            'initialized': self._initialized,
            'engine_connected': False,
            'error': None
        }
        
        try:
            if self.engine:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                    result['engine_connected'] = True
                    result['status'] = 'healthy'
        except Exception as e:
            result['error'] = str(e)
        
        return result
    
    def execute_raw_sql(self, sql: str, params: Optional[dict] = None) -> bool:
        """
        Execute raw SQL (use with caution!)
        
        Args:
            sql: SQL statement to execute
            params: Query parameters
            
        Returns:
            True if successful, False otherwise
        """
        if not self.engine:
            logger.error("Database engine not initialized")
            return False
        
        try:
            with self.engine.connect() as conn:
                conn.execute(text(sql), params or {})
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Failed to execute SQL: {e}")
            return False

# Global database manager instance
db_manager = DatabaseManager()

# Convenience functions
def get_db_session() -> Generator[Session, None, None]:
    """Get database session (context manager)"""
    return db_manager.get_session()

def init_database(database_url: Optional[str] = None, create_tables: bool = True, echo: bool = False) -> bool:
    """
    Initialize database with optional custom URL
    
    Args:
        database_url: Custom database URL
        create_tables: Whether to create tables
        echo: Whether to echo SQL statements
        
    Returns:
        True if initialization successful
    """
    if database_url:
        global db_manager
        db_manager = DatabaseManager(database_url)
    
    return db_manager.initialize(create_tables=create_tables, echo=echo)

def close_database():
    """Close database connection"""
    db_manager.close()

def database_health_check() -> dict:
    """Get database health status"""
    return db_manager.health_check()

# Database utility functions
class DatabaseUtils:
    """Utility functions for database operations"""
    
    @staticmethod
    def setup_test_database(test_db_url: str = "postgresql://postgres:postgres@localhost:5432/test_orbital_ballet"):
        """Setup test database"""
        test_manager = DatabaseManager(test_db_url)
        return test_manager.initialize(create_tables=True)
    
    @staticmethod
    def backup_database(backup_file: str) -> bool:
        """Create database backup (requires pg_dump)"""
        try:
            import subprocess
            cmd = f"pg_dump {db_manager.database_url} > {backup_file}"
            subprocess.run(cmd, shell=True, check=True)
            logger.info(f"Database backup created: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return False
    
    @staticmethod
    def restore_database(backup_file: str) -> bool:
        """Restore database from backup (requires psql)"""
        try:
            import subprocess
            cmd = f"psql {db_manager.database_url} < {backup_file}"
            subprocess.run(cmd, shell=True, check=True)
            logger.info(f"Database restored from: {backup_file}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False
    
    @staticmethod
    def get_table_stats() -> dict:
        """Get database table statistics"""
        stats = {}
        try:
            with get_db_session() as session:
                from .models import (
                    TLEData, Satellite, DebrisObject, OrbitalState,
                    RiskAssessment, CollisionPrediction, ManeuverPlan, SystemLog
                )
                
                stats['tle_data'] = session.query(TLEData).count()
                stats['satellites'] = session.query(Satellite).count()
                stats['debris_objects'] = session.query(DebrisObject).count()
                stats['orbital_states'] = session.query(OrbitalState).count()
                stats['risk_assessments'] = session.query(RiskAssessment).count()
                stats['collision_predictions'] = session.query(CollisionPrediction).count()
                stats['maneuver_plans'] = session.query(ManeuverPlan).count()
                stats['system_logs'] = session.query(SystemLog).count()
                
        except Exception as e:
            logger.error(f"Failed to get table stats: {e}")
        
        return stats

# Example usage and initialization
if __name__ == "__main__":
    # Initialize database
    success = init_database(echo=True, create_tables=True)
    
    if success:
        print("Database initialized successfully!")
        
        # Health check
        health = database_health_check()
        print(f"Database health: {health}")
        
        # Get table statistics
        stats = DatabaseUtils.get_table_stats()
        print(f"Table statistics: {stats}")
        
    else:
        print("Failed to initialize database")
    
    # Close when done
    close_database()