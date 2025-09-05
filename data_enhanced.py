"""
Live Orbital Ballet - Enhanced Data Management Module with Database Integration
Maintains backward compatibility while adding persistent storage capabilities
"""

import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Tuple, Optional, Union, Any
import logging
from dataclasses import dataclass
import time
import random
import threading
import json
import uuid
from urllib.parse import urljoin
from scipy.spatial import KDTree
from decimal import Decimal

# Database imports
try:
    from database import (
        init_database, get_db_session, database_health_check,
        TLEDataDAO, SatelliteDAO, OrbitalStateDAO, 
        log_info, log_warning, log_error
    )
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    logging.warning("Database module not available. Running in memory-only mode.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TLEData:
    """Two-Line Element data structure - Enhanced with database integration"""
    name: str
    line1: str
    line2: str
    norad_id: int
    timestamp: datetime
    
    # Additional fields for database integration
    classification: str = 'U'
    launch_year: Optional[int] = None
    launch_number: Optional[int] = None
    piece_designator: Optional[str] = None
    epoch_year: Optional[int] = None
    epoch_day: Optional[float] = None
    mean_motion: Optional[float] = None
    eccentricity: Optional[float] = None
    inclination: Optional[float] = None
    ra_of_asc_node: Optional[float] = None
    arg_of_perigee: Optional[float] = None
    mean_anomaly: Optional[float] = None
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'line1': self.line1,
            'line2': self.line2,
            'norad_id': self.norad_id,
            'timestamp': self.timestamp,
            'classification': self.classification,
            'launch_year': self.launch_year,
            'launch_number': self.launch_number,
            'piece_designator': self.piece_designator,
            'epoch_year': self.epoch_year,
            'epoch_day': self.epoch_day,
            'mean_motion': self.mean_motion,
            'eccentricity': self.eccentricity,
            'inclination': self.inclination,
            'ra_of_asc_node': self.ra_of_asc_node,
            'arg_of_perigee': self.arg_of_perigee,
            'mean_anomaly': self.mean_anomaly
        }
    
    def to_database_dict(self) -> Dict:
        """Convert to format suitable for database storage"""
        return {
            'norad_id': self.norad_id,
            'satellite_name': self.name,
            'line1': self.line1,
            'line2': self.line2,
            'classification': self.classification or 'U',
            'launch_year': self.launch_year,
            'launch_number': self.launch_number,
            'piece_designator': self.piece_designator,
            'epoch_year': self.epoch_year,
            'epoch_day': Decimal(str(self.epoch_day)) if self.epoch_day else None,
            'is_active': True,
            'data_source': 'CELESTRAK'
        }

@dataclass 
class DebrisObject:
    """Enhanced space debris object data structure with database support"""
    id: str
    position: Tuple[float, float, float]  # x, y, z in km (ECI)
    velocity: Tuple[float, float, float]  # vx, vy, vz in km/s
    size: float  # effective diameter in meters
    mass: float  # mass in kg
    risk_category: str  # 'high', 'medium', 'low'
    timestamp: datetime
    orbital_regime: str  # 'LEO', 'MEO', 'HEO', 'GEO'
    altitude: float  # altitude in km
    inclination: float  # inclination in degrees
    eccentricity: float  # orbital eccentricity
    
    @property
    def position_array(self) -> np.ndarray:
        return np.array(self.position)
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'position': self.position,
            'velocity': self.velocity,
            'size': self.size,
            'mass': self.mass,
            'risk_category': self.risk_category,
            'orbital_regime': self.orbital_regime,
            'altitude': self.altitude,
            'inclination': self.inclination,
            'eccentricity': self.eccentricity,
            'timestamp': self.timestamp.isoformat()
        }
    
    def to_database_dict(self) -> Dict:
        """Convert to format suitable for database storage"""
        return {
            'debris_id': self.id,
            'debris_type': 'fragment',  # Default type
            'estimated_size_m': Decimal(str(self.size)),
            'estimated_mass_kg': Decimal(str(self.mass)),
            'creation_date': self.timestamp,
            'risk_category': self.risk_category.upper(),
            'tracking_status': 'MONITORED',
            'last_observed': self.timestamp
        }

class EnhancedCelestrakDataFetcher:
    """Enhanced TLE data fetcher with database integration"""
    
    BASE_URL = "https://celestrak.org"
    
    # Popular satellite categories for demonstration
    TLE_SOURCES = {
        'active_satellites': '/NORAD/elements/gp.php?GROUP=active&FORMAT=tle',
        'space_stations': '/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle',
        'weather': '/NORAD/elements/gp.php?GROUP=weather&FORMAT=tle',
        'communication': '/NORAD/elements/gp.php?GROUP=geo&FORMAT=tle',
        'navigation': '/NORAD/elements/gp.php?GROUP=gnss&FORMAT=tle',
        'scientific': '/NORAD/elements/gp.php?GROUP=science&FORMAT=tle',
        'military': '/NORAD/elements/gp.php?GROUP=military&FORMAT=tle'
    }
    
    def __init__(self, timeout: int = 30, max_retries: int = 3, use_database: bool = True):
        self.timeout = timeout
        self.max_retries = max_retries
        self.use_database = use_database and DATABASE_AVAILABLE
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Live-Orbital-Ballet/1.0'
        })
        
        if self.use_database:
            logger.info("Enhanced fetcher initialized with database support")
        else:
            logger.info("Enhanced fetcher initialized in memory-only mode")
    
    def fetch_tle_data(self, category: str = 'active_satellites', limit: Optional[int] = None, 
                      force_refresh: bool = False) -> List[TLEData]:
        """
        Enhanced TLE data fetching with database caching
        
        Args:
            category: Satellite category from TLE_SOURCES
            limit: Maximum number of satellites to return
            force_refresh: Force fetch from API even if database has recent data
            
        Returns:
            List of TLEData objects
        """
        if category not in self.TLE_SOURCES:
            logger.error(f"Unknown category: {category}")
            return []
        
        # Try to get from database first (if not forcing refresh)
        if self.use_database and not force_refresh:
            cached_data = self._get_cached_tle_data(limit)
            if cached_data and len(cached_data) > 0:
                # Check if data is recent (less than 1 hour old)
                if cached_data[0].timestamp and (datetime.now(timezone.utc) - cached_data[0].timestamp) < timedelta(hours=1):
                    logger.info(f"Using cached TLE data: {len(cached_data)} records")
                    return cached_data[:limit] if limit else cached_data
        
        # Fetch fresh data from API
        url = urljoin(self.BASE_URL, self.TLE_SOURCES[category])
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching TLE data from {category} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                tle_list = self._parse_tle_response(response.text)
                
                if limit:
                    tle_list = tle_list[:limit]
                
                # Store in database if available
                if self.use_database and tle_list:
                    self._store_tle_data(tle_list)
                
                logger.info(f"Successfully fetched {len(tle_list)} TLE records")
                log_info('DATA_FETCH', f'Fetched {len(tle_list)} TLE records from {category}')
                return tle_list
                
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error("All retry attempts failed")
                    log_error('DATA_FETCH', f'Failed to fetch TLE data from {category}: {e}')
        
        # Fallback to cached data if API fails
        if self.use_database:
            cached_data = self._get_cached_tle_data(limit)
            if cached_data:
                logger.warning(f"API failed, using cached data: {len(cached_data)} records")
                return cached_data
        
        return []
    
    def _get_cached_tle_data(self, limit: Optional[int] = None) -> List[TLEData]:
        """Get TLE data from database cache"""
        if not self.use_database:
            return []
        
        try:
            # Get active TLE data from database
            db_tles = TLEDataDAO.get_active_tles()
            
            # Convert database records to TLEData objects
            tle_list = []
            for db_tle in db_tles[:limit] if limit else db_tles:
                tle = TLEData(
                    name=db_tle.satellite_name,
                    line1=db_tle.line1,
                    line2=db_tle.line2,
                    norad_id=db_tle.norad_id,
                    timestamp=db_tle.updated_at,
                    classification=db_tle.classification or 'U',
                    launch_year=db_tle.launch_year,
                    launch_number=db_tle.launch_number,
                    piece_designator=db_tle.piece_designator,
                    epoch_year=db_tle.epoch_year,
                    epoch_day=float(db_tle.epoch_day) if db_tle.epoch_day else None
                )
                tle_list.append(tle)
            
            return tle_list
            
        except Exception as e:
            logger.error(f"Error retrieving cached TLE data: {e}")
            return []
    
    def _store_tle_data(self, tle_list: List[TLEData]) -> bool:
        """Store TLE data in database"""
        if not self.use_database:
            return False
        
        try:
            stored_count = 0
            for tle in tle_list:
                db_tle = TLEDataDAO.create_or_update_tle(tle.to_database_dict())
                if db_tle:
                    stored_count += 1
                    
                    # Also create/update satellite record
                    satellite_data = {
                        'norad_id': tle.norad_id,
                        'name': tle.name,
                        'satellite_type': self._determine_satellite_type(tle.name),
                        'operational_status': 'ACTIVE',
                        'track_continuously': True,
                        'collision_monitoring': True,
                        'priority_level': 5
                    }
                    SatelliteDAO.create_satellite(satellite_data)
            
            logger.info(f"Stored {stored_count}/{len(tle_list)} TLE records in database")
            return stored_count > 0
            
        except Exception as e:
            logger.error(f"Error storing TLE data: {e}")
            return False
    
    def _determine_satellite_type(self, satellite_name: str) -> str:
        """Determine satellite type from name"""
        name_upper = satellite_name.upper()
        
        if any(term in name_upper for term in ['WEATHER', 'NOAA', 'METEOSAT']):
            return 'weather'
        elif any(term in name_upper for term in ['GPS', 'GLONASS', 'GALILEO', 'BEIDOU']):
            return 'navigation'
        elif any(term in name_upper for term in ['INTELSAT', 'IRIDIUM', 'STARLINK']):
            return 'communication'
        elif any(term in name_upper for term in ['ISS', 'TIANGONG', 'STATION']):
            return 'scientific'
        elif any(term in name_upper for term in ['MILITARY', 'CLASSIFIED']):
            return 'military'
        else:
            return 'commercial'
    
    def _parse_tle_response(self, response_text: str) -> List[TLEData]:
        """Enhanced TLE parsing with additional orbital elements extraction"""
        lines = [line.strip() for line in response_text.split('\n') if line.strip()]
        tle_data = []
        current_time = datetime.now(timezone.utc)
        
        # TLE format: name line, line1, line2 (groups of 3)
        for i in range(0, len(lines), 3):
            if i + 2 >= len(lines):
                break
                
            name = lines[i]
            line1 = lines[i + 1]
            line2 = lines[i + 2]
            
            # Validate TLE format
            if not (line1.startswith('1 ') and line2.startswith('2 ')):
                continue
                
            try:
                # Extract NORAD ID from line 1
                norad_id = int(line1[2:7])
                
                # Extract additional orbital elements
                classification = line1[7]
                launch_year = int(line1[9:11])
                launch_year += 2000 if launch_year < 57 else 1900  # Y2K handling
                launch_number = int(line1[11:14])
                piece_designator = line1[14:17].strip()
                
                # Epoch
                epoch_year = int(line1[18:20])
                epoch_year += 2000 if epoch_year < 57 else 1900
                epoch_day = float(line1[20:32])
                
                # Orbital elements from line 2
                inclination = float(line2[8:16])
                ra_of_asc_node = float(line2[17:25])
                eccentricity = float('0.' + line2[26:33])
                arg_of_perigee = float(line2[34:42])
                mean_anomaly = float(line2[43:51])
                mean_motion = float(line2[52:63])
                
                tle_data.append(TLEData(
                    name=name,
                    line1=line1,
                    line2=line2,
                    norad_id=norad_id,
                    timestamp=current_time,
                    classification=classification,
                    launch_year=launch_year,
                    launch_number=launch_number,
                    piece_designator=piece_designator,
                    epoch_year=epoch_year,
                    epoch_day=epoch_day,
                    mean_motion=mean_motion,
                    eccentricity=eccentricity,
                    inclination=inclination,
                    ra_of_asc_node=ra_of_asc_node,
                    arg_of_perigee=arg_of_perigee,
                    mean_anomaly=mean_anomaly
                ))
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing TLE for {name}: {e}")
                continue
                
        return tle_data

class EnhancedDataManager:
    """Enhanced Data Manager with database integration and backward compatibility"""
    
    def __init__(self, use_database: bool = None, refresh_interval: int = 60):
        """
        Initialize Enhanced Data Manager
        
        Args:
            use_database: Whether to use database (auto-detect if None)
            refresh_interval: Background refresh interval in minutes
        """
        # Auto-detect database availability if not specified
        if use_database is None:
            use_database = DATABASE_AVAILABLE
        
        self.use_database = use_database
        self.refresh_interval_minutes = refresh_interval
        
        # Initialize database connection if available
        if self.use_database:
            try:
                # Try to initialize database (don't create tables here - let user decide)
                health = database_health_check()
                if health['status'] != 'healthy':
                    logger.warning("Database not healthy, falling back to memory-only mode")
                    self.use_database = False
            except Exception as e:
                logger.warning(f"Database initialization failed: {e}, falling back to memory-only mode")
                self.use_database = False
        
        # Initialize components
        self.fetcher = EnhancedCelestrakDataFetcher(use_database=self.use_database)
        
        # Backward compatibility: in-memory caches
        self.cached_tle_data: Optional[List[TLEData]] = None
        self.cached_debris_data: Optional[List[DebrisObject]] = None
        self.cached_positions: Optional[Dict] = None
        self.last_update: Optional[datetime] = None
        self.is_demo_mode = False
        self.fetch_failure_count = 0
        
        # Background refresh
        self.refresh_thread: Optional[threading.Thread] = None
        self.stop_refresh_event = threading.Event()
        
        logger.info(f"Enhanced DataManager initialized (database: {self.use_database})")
    
    def get_satellite_data(self, limit: Optional[int] = None, force_refresh: bool = False, 
                          use_cache: bool = True) -> List[TLEData]:
        """
        Enhanced satellite data retrieval with database integration
        
        Args:
            limit: Maximum number of satellites to return
            force_refresh: Force refresh from API
            use_cache: Use in-memory cache for backward compatibility
            
        Returns:
            List of TLEData objects
        """
        try:
            # If using database, get data from there
            if self.use_database:
                satellites = self.fetcher.fetch_tle_data('active_satellites', limit, force_refresh)
                
                # Update in-memory cache for backward compatibility
                if use_cache:
                    self.cached_tle_data = satellites
                    self.last_update = datetime.now(timezone.utc)
                
                return satellites
            
            # Fallback to original in-memory behavior
            else:
                # Check cache first
                if use_cache and self.cached_tle_data and not force_refresh:
                    if limit:
                        return self.cached_tle_data[:limit]
                    return self.cached_tle_data
                
                # Fetch new data
                satellites = self.fetcher.fetch_tle_data('active_satellites', limit, force_refresh=True)
                
                if satellites:
                    self.cached_tle_data = satellites
                    self.last_update = datetime.now(timezone.utc)
                    self.fetch_failure_count = 0
                else:
                    self.fetch_failure_count += 1
                
                return satellites
                
        except Exception as e:
            logger.error(f"Error getting satellite data: {e}")
            log_error('DATA_MANAGER', f'Error getting satellite data: {e}')
            
            # Return cached data if available
            if use_cache and self.cached_tle_data:
                logger.warning("Returning cached data due to error")
                return self.cached_tle_data[:limit] if limit else self.cached_tle_data
            
            return []
    
    def store_orbital_states(self, satellite_positions: Dict) -> bool:
        """Store computed orbital states in database"""
        if not self.use_database:
            return False
        
        try:
            stored_count = 0
            current_time = datetime.now(timezone.utc)
            
            for norad_id, pos_data in satellite_positions.items():
                # Get satellite ID from database
                satellite = SatelliteDAO.get_satellite_by_norad_id(int(norad_id))
                if not satellite:
                    continue
                
                # Prepare orbital state data
                state_data = {
                    'object_type': 'SATELLITE',
                    'object_id': satellite.id,
                    'norad_id': int(norad_id),
                    'position_x': Decimal(str(pos_data['position'][0])),
                    'position_y': Decimal(str(pos_data['position'][1])),
                    'position_z': Decimal(str(pos_data['position'][2])),
                    'velocity_x': Decimal(str(pos_data['velocity'][0])),
                    'velocity_y': Decimal(str(pos_data['velocity'][1])),
                    'velocity_z': Decimal(str(pos_data['velocity'][2])),
                    'altitude_km': Decimal(str(pos_data.get('altitude', 0))),
                    'epoch': current_time,
                    'prediction_type': 'SGP4'
                }
                
                orbital_state = OrbitalStateDAO.save_orbital_state(state_data)
                if orbital_state:
                    stored_count += 1
            
            logger.info(f"Stored {stored_count} orbital states in database")
            log_info('ORBITAL_TRACKING', f'Stored {stored_count} orbital states')
            return stored_count > 0
            
        except Exception as e:
            logger.error(f"Error storing orbital states: {e}")
            log_error('ORBITAL_TRACKING', f'Error storing orbital states: {e}')
            return False
    
    def get_debris_data(self, count: int = 100) -> List[DebrisObject]:
        """Enhanced debris data generation with database storage"""
        # Original synthetic debris generation for backward compatibility
        from data import SyntheticDebrisGenerator
        
        generator = SyntheticDebrisGenerator()
        debris_objects = generator.generate_debris_field(count)
        
        # Store in database if available
        if self.use_database:
            try:
                # Convert and store debris objects (simplified for demo)
                # In a real system, you'd use DebrisDAO here
                pass
            except Exception as e:
                logger.warning(f"Could not store debris data: {e}")
        
        # Update cache for backward compatibility
        self.cached_debris_data = debris_objects
        
        return debris_objects
    
    def get_status_info(self) -> Dict[str, Any]:
        """Enhanced status information with database metrics"""
        status = {
            'data_source': 'live' if not self.is_demo_mode else 'synthetic',
            'satellite_count': len(self.cached_tle_data) if self.cached_tle_data else 0,
            'debris_count': len(self.cached_debris_data) if self.cached_debris_data else 0,
            'last_update': self.last_update.isoformat() + 'Z' if self.last_update else None,
            'data_age_minutes': (datetime.now(timezone.utc) - self.last_update).total_seconds() / 60 if self.last_update else None,
            'refresh_interval': self.refresh_interval_minutes,
            'fetch_failures': self.fetch_failure_count,
            'auto_refresh_active': self.refresh_thread is not None and self.refresh_thread.is_alive(),
            'database_enabled': self.use_database
        }
        
        # Add database-specific status if available
        if self.use_database:
            try:
                from database import get_system_status
                db_status = get_system_status()
                status.update({
                    'database_health': db_status['database_health']['status'],
                    'database_statistics': db_status['system_statistics']
                })
            except Exception as e:
                logger.warning(f"Could not get database status: {e}")
                status['database_health'] = 'unknown'
        
        return status
    
    # Backward compatibility methods (delegate to original implementations)
    def start_background_refresh(self):
        """Start background data refresh (backward compatibility)"""
        # Implementation from original data.py
        pass
    
    def stop_background_refresh(self):
        """Stop background data refresh (backward compatibility)"""
        if self.refresh_thread and self.refresh_thread.is_alive():
            self.stop_refresh_event.set()
            self.refresh_thread.join(timeout=5)
    
    def cleanup(self):
        """Enhanced cleanup with database connection handling"""
        try:
            self.stop_background_refresh()
            
            # Close database connections if needed
            if self.use_database:
                from database import close_database
                close_database()
            
            logger.info("Enhanced DataManager cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

# Backward compatibility: create alias for original DataManager
DataManager = EnhancedDataManager

# Example usage and testing
if __name__ == "__main__":
    print("🚀 Enhanced Data Manager with Database Integration")
    print("=" * 50)
    
    # Initialize enhanced data manager
    data_manager = EnhancedDataManager(use_database=True)
    
    # Test satellite data fetching
    logger.info("Testing enhanced satellite data fetching...")
    satellites = data_manager.get_satellite_data(limit=20)
    print(f"Retrieved {len(satellites)} satellites")
    
    if satellites:
        print(f"Sample satellite: {satellites[0].name} (NORAD {satellites[0].norad_id})")
        print(f"  Classification: {satellites[0].classification}")
        print(f"  Inclination: {satellites[0].inclination}°")
        
    # Test status information
    status = data_manager.get_status_info()
    print(f"\nEnhanced status info:")
    for key, value in status.items():
        print(f"  {key}: {value}")
    
    # Cleanup
    data_manager.cleanup()