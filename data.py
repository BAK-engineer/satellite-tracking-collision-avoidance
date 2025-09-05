"""
Live Orbital Ballet - Data Management Module
Handles TLE data fetching from Celestrak and synthetic debris generation
"""

import requests
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Union, Any
import logging
from dataclasses import dataclass
import time
import random
import threading
import json
from urllib.parse import urljoin
from scipy.spatial import KDTree

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TLEData:
    """Two-Line Element data structure"""
    name: str
    line1: str
    line2: str
    norad_id: int
    timestamp: datetime
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'line1': self.line1,
            'line2': self.line2,
            'norad_id': self.norad_id,
            'timestamp': self.timestamp
        }

@dataclass 
class DebrisObject:
    """Enhanced space debris object data structure"""
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

class CelestrakDataFetcher:
    """Fetches TLE data from Celestrak APIs"""
    
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
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Live-Orbital-Ballet/1.0'
        })
        
    def fetch_tle_data(self, category: str = 'active_satellites', limit: Optional[int] = None) -> List[TLEData]:
        """
        Fetch TLE data from Celestrak for specified category
        
        Args:
            category: Satellite category from TLE_SOURCES
            limit: Maximum number of satellites to return
            
        Returns:
            List of TLEData objects
        """
        if category not in self.TLE_SOURCES:
            logger.error(f"Unknown category: {category}")
            return []
            
        url = urljoin(self.BASE_URL, self.TLE_SOURCES[category])
        
        for attempt in range(self.max_retries):
            try:
                logger.info(f"Fetching TLE data from {category} (attempt {attempt + 1})")
                response = self.session.get(url, timeout=self.timeout)
                response.raise_for_status()
                
                tle_list = self._parse_tle_response(response.text)
                
                if limit:
                    tle_list = tle_list[:limit]
                    
                logger.info(f"Successfully fetched {len(tle_list)} TLE records")
                return tle_list
                
            except requests.RequestException as e:
                logger.warning(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error("All retry attempts failed")
                    
        return []
    
    def _parse_tle_response(self, response_text: str) -> List[TLEData]:
        """Parse TLE format response into TLEData objects"""
        lines = [line.strip() for line in response_text.split('\n') if line.strip()]
        tle_data = []
        current_time = datetime.utcnow()
        
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
                
                tle_data.append(TLEData(
                    name=name,
                    line1=line1,
                    line2=line2,
                    norad_id=norad_id,
                    timestamp=current_time
                ))
            except (ValueError, IndexError) as e:
                logger.warning(f"Error parsing TLE for {name}: {e}")
                continue
                
        return tle_data
    
    def fetch_multiple_categories(self, categories: List[str], limit_per_category: int = 50) -> List[TLEData]:
        """Fetch TLE data from multiple categories"""
        all_tle_data = []
        
        for category in categories:
            tle_data = self.fetch_tle_data(category, limit_per_category)
            all_tle_data.extend(tle_data)
            time.sleep(0.5)  # Be respectful to the API
            
        return all_tle_data

class SyntheticDebrisGenerator:
    """Generates synthetic space debris for hackathon demonstrations"""
    
    # Orbital regime definitions (altitude ranges in km)
    ORBITAL_REGIMES = {
        'LEO': (200, 2000),      # Low Earth Orbit
        'MEO': (2000, 35786),    # Medium Earth Orbit  
        'HEO': (35786, 100000),  # High Earth Orbit
        'GEO': (35786, 35786)    # Geostationary
    }
    
    def __init__(self, seed: Optional[int] = None):
        if seed is not None:
            random.seed(seed)
            np.random.seed(seed)
        self.earth_radius = 6371.0  # km
    
    def generate_debris_field(self, num_objects: int = 100, 
                            regime_distribution: Optional[Dict[str, float]] = None) -> List[DebrisObject]:
        """
        Generate synthetic debris objects across realistic orbital regimes
        
        Args:
            num_objects: Number of debris objects to generate
            regime_distribution: Distribution across orbital regimes
            
        Returns:
            List of DebrisObject instances with realistic orbits
        """
        if regime_distribution is None:
            regime_distribution = {
                'LEO': 0.7,   # 70% in LEO (most debris)
                'MEO': 0.2,   # 20% in MEO
                'HEO': 0.08,  # 8% in HEO
                'GEO': 0.02   # 2% in GEO
            }
        
        debris_objects = []
        current_time = datetime.utcnow()
        
        # Distribute objects across orbital regimes
        for regime, fraction in regime_distribution.items():
            regime_count = int(num_objects * fraction)
            regime_objects = self._generate_regime_debris(regime, regime_count, current_time)
            debris_objects.extend(regime_objects)
            
        # Generate any remaining objects in LEO
        remaining = num_objects - len(debris_objects)
        if remaining > 0:
            remaining_objects = self._generate_regime_debris('LEO', remaining, current_time)
            debris_objects.extend(remaining_objects)
            
        logger.info(f"Generated {len(debris_objects)} synthetic debris objects across orbital regimes")
        return debris_objects
    
    def generate_collision_scenarios(self, satellites: List[TLEData], 
                                   num_scenarios: int = 5) -> List[DebrisObject]:
        """Generate debris objects that will create collision scenarios for demo"""
        collision_debris = []
        
        if not satellites:
            return collision_debris
            
        # Take a subset of satellites to create collision scenarios
        target_satellites = satellites[:min(num_scenarios, len(satellites))]
        
        for i, satellite in enumerate(target_satellites):
            # Generate debris near satellite orbit for guaranteed close approach
            # This is a simplified approach for demonstration
            debris_id = f"COLLISION_DEBRIS_{i:03d}"
            
            # Use synthetic position near satellite's typical orbit
            # For demo purposes, place debris in collision course
            base_altitude = 500 + i * 100  # Vary altitude
            position, velocity = self._generate_collision_course(base_altitude)
            
            debris = DebrisObject(
                id=debris_id,
                position=position,
                velocity=velocity,
                size=np.random.uniform(0.1, 2.0),  # Medium to large debris
                mass=np.random.uniform(10, 1000),
                risk_category='high',  # Always high risk for demo
                timestamp=datetime.utcnow(),
                orbital_regime='LEO',
                altitude=base_altitude,
                inclination=np.random.uniform(0, 180),
                eccentricity=np.random.exponential(0.05)
            )
            
            collision_debris.append(debris)
            
        logger.info(f"Generated {len(collision_debris)} collision scenario debris objects")
        return collision_debris
    
    def _generate_collision_course(self, altitude: float) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """Generate position/velocity for debris on collision course"""
        r = self.earth_radius + altitude
        
        # Random position on sphere
        theta = np.random.uniform(0, 2 * np.pi)
        phi = np.random.uniform(0, np.pi)
        
        x = r * np.sin(phi) * np.cos(theta)
        y = r * np.sin(phi) * np.sin(theta)
        z = r * np.cos(phi)
        
        # Velocity with some randomness to create collision scenario
        v_mag = np.sqrt(398600.4418 / r)  # Circular velocity
        
        # Add perturbation to create collision course
        v_theta = theta + np.pi/2 + np.random.normal(0, 0.2)  # More randomness
        v_phi = np.pi/2 + np.random.normal(0, 0.1)
        
        vx = v_mag * np.sin(v_phi) * np.cos(v_theta)
        vy = v_mag * np.sin(v_phi) * np.sin(v_theta)
        vz = v_mag * np.cos(v_phi)
        
        return (x, y, z), (vx, vy, vz)
    
    def _generate_regime_debris(self, regime: str, count: int, timestamp: datetime) -> List[DebrisObject]:
        """Generate debris objects for a specific orbital regime"""
        objects = []
        alt_min, alt_max = self.ORBITAL_REGIMES[regime]
        
        for i in range(count):
            # Generate orbital parameters for regime
            if regime == 'GEO':
                altitude = 35786  # Fixed GEO altitude
                inclination = np.random.normal(0, 3)  # Near-equatorial
                eccentricity = np.random.exponential(0.02)  # Nearly circular
            elif regime == 'LEO':
                altitude = np.random.uniform(alt_min, alt_max)
                inclination = np.random.uniform(0, 180)  # All inclinations
                eccentricity = np.random.exponential(0.05)  # Mostly circular
            elif regime == 'MEO':
                altitude = np.random.uniform(alt_min, alt_max)
                inclination = np.random.uniform(0, 90)  # Prefer lower inclinations
                eccentricity = np.random.exponential(0.1)  # Some ellipticity
            else:  # HEO
                altitude = np.random.uniform(alt_min, alt_max)
                inclination = np.random.uniform(0, 180)
                eccentricity = np.random.uniform(0.1, 0.7)  # Highly elliptical
            
            # Calculate position and velocity
            position, velocity = self._generate_orbital_state(altitude, inclination, eccentricity)
            
            # Generate debris characteristics
            size = self._generate_debris_size()
            mass = self._estimate_mass_from_size(size)
            risk_category = self._categorize_risk(size, altitude)
            
            debris = DebrisObject(
                id=f"DEBRIS_{regime}_{i:04d}",
                position=position,
                velocity=velocity,
                size=size,
                mass=mass,
                risk_category=risk_category,
                timestamp=timestamp,
                orbital_regime=regime,
                altitude=altitude,
                inclination=inclination,
                eccentricity=eccentricity
            )
            
            objects.append(debris)
            
        return objects
    
    def _generate_orbital_state(self, altitude: float, inclination: float, 
                              eccentricity: float) -> Tuple[Tuple[float, float, float], Tuple[float, float, float]]:
        """Generate realistic position and velocity for given orbital parameters"""
        # Semi-major axis
        a = self.earth_radius + altitude
        
        # Random true anomaly (position in orbit)
        true_anomaly = np.random.uniform(0, 2 * np.pi)
        
        # Random argument of perigee and RAAN
        arg_perigee = np.random.uniform(0, 2 * np.pi)
        raan = np.random.uniform(0, 2 * np.pi)
        
        # Calculate radius at true anomaly
        r = a * (1 - eccentricity**2) / (1 + eccentricity * np.cos(true_anomaly))
        
        # Position in orbital plane
        x_orbit = r * np.cos(true_anomaly)
        y_orbit = r * np.sin(true_anomaly)
        z_orbit = 0
        
        # Velocity in orbital plane (simplified)
        mu = 398600.4418  # Earth's gravitational parameter
        h = np.sqrt(mu * a * (1 - eccentricity**2))  # Specific angular momentum
        
        vx_orbit = -mu * np.sin(true_anomaly) / h
        vy_orbit = mu * (eccentricity + np.cos(true_anomaly)) / h
        vz_orbit = 0
        
        # Transform to ECI coordinates using rotation matrices
        # This is a simplified transformation
        incl_rad = np.radians(inclination)
        raan_rad = raan
        argp_rad = arg_perigee
        
        # Rotation matrices (simplified)
        cos_raan, sin_raan = np.cos(raan_rad), np.sin(raan_rad)
        cos_incl, sin_incl = np.cos(incl_rad), np.sin(incl_rad)
        cos_argp, sin_argp = np.cos(argp_rad), np.sin(argp_rad)
        
        # Position transformation
        x = (cos_raan * cos_argp - sin_raan * sin_argp * cos_incl) * x_orbit + \
            (-cos_raan * sin_argp - sin_raan * cos_argp * cos_incl) * y_orbit
        y = (sin_raan * cos_argp + cos_raan * sin_argp * cos_incl) * x_orbit + \
            (-sin_raan * sin_argp + cos_raan * cos_argp * cos_incl) * y_orbit
        z = (sin_argp * sin_incl) * x_orbit + (cos_argp * sin_incl) * y_orbit
        
        # Velocity transformation (simplified)
        vx = (cos_raan * cos_argp - sin_raan * sin_argp * cos_incl) * vx_orbit + \
             (-cos_raan * sin_argp - sin_raan * cos_argp * cos_incl) * vy_orbit
        vy = (sin_raan * cos_argp + cos_raan * sin_argp * cos_incl) * vx_orbit + \
             (-sin_raan * sin_argp + cos_raan * cos_argp * cos_incl) * vy_orbit
        vz = (sin_argp * sin_incl) * vx_orbit + (cos_argp * sin_incl) * vy_orbit
        
        return (x, y, z), (vx, vy, vz)
    
    def _generate_debris_size(self) -> float:
        """Generate realistic debris size distribution (Kessler syndrome inspired)"""
        # Power law distribution for space debris sizes
        # Most debris is small, few large pieces
        size_categories = [
            (0.001, 0.01, 0.7),   # micro debris (1mm-1cm) - 70%
            (0.01, 0.1, 0.2),     # small debris (1-10cm) - 20% 
            (0.1, 1.0, 0.08),     # medium debris (10cm-1m) - 8%
            (1.0, 10.0, 0.02)     # large debris (1-10m) - 2%
        ]
        
        category = np.random.choice(len(size_categories), 
                                  p=[cat[2] for cat in size_categories])
        min_size, max_size, _ = size_categories[category]
        
        return np.random.uniform(min_size, max_size)
    
    def _estimate_mass_from_size(self, size: float) -> float:
        """Estimate debris mass from size assuming typical materials"""
        # Assume spherical debris with typical space material density
        volume = (4/3) * np.pi * (size/2)**3  # m³
        density = np.random.uniform(2000, 8000)  # kg/m³ (aluminum to steel)
        return volume * density
    
    def _categorize_risk(self, size: float, altitude: float) -> str:
        """Categorize debris risk level"""
        # Risk factors: size and orbital decay probability
        risk_score = 0
        
        # Size risk
        if size > 1.0:
            risk_score += 3
        elif size > 0.1:
            risk_score += 2
        elif size > 0.01:
            risk_score += 1
            
        # Altitude risk (lower = faster decay = less long-term risk)
        if altitude < 400:
            risk_score -= 1
        elif altitude > 800:
            risk_score += 1
            
        if risk_score >= 3:
            return 'high'
        elif risk_score >= 1:
            return 'medium'
        else:
            return 'low'

class DataManager:
    """Enhanced data management with automatic refresh and fallback"""
    
    def __init__(self, use_synthetic_fallback: bool = True, auto_refresh: bool = True):
        self.fetcher = CelestrakDataFetcher()
        self.debris_generator = SyntheticDebrisGenerator()
        self.use_synthetic_fallback = use_synthetic_fallback
        self.auto_refresh = auto_refresh
        
        # Data caches
        self.cached_tle_data = []
        self.cached_debris_data = []
        self.synthetic_satellites = []
        self.last_update = None
        self.last_fetch_attempt = None
        self.fetch_failure_count = 0
        self.is_demo_mode = False
        
        # Refresh settings
        self.refresh_interval_minutes = 30
        self.max_fetch_failures = 3
        
        # Threading for background refresh
        self.refresh_thread = None
        self.stop_refresh = False
        
        if auto_refresh:
            self.start_background_refresh()
    
    def start_background_refresh(self):
        """Start background thread for automatic data refresh"""
        if self.refresh_thread is None or not self.refresh_thread.is_alive():
            self.stop_refresh = False
            self.refresh_thread = threading.Thread(target=self._background_refresh_worker, daemon=True)
            self.refresh_thread.start()
            logger.info("Started background data refresh thread")
    
    def stop_background_refresh(self):
        """Stop background refresh thread"""
        self.stop_refresh = True
        if self.refresh_thread and self.refresh_thread.is_alive():
            self.refresh_thread.join(timeout=5)
            logger.info("Stopped background data refresh thread")
    
    def _background_refresh_worker(self):
        """Background worker for automatic data refresh"""
        while not self.stop_refresh:
            try:
                # Check if refresh is needed
                if self._needs_refresh():
                    logger.info("Background refresh triggered")
                    self.refresh_satellite_data()
                
                # Sleep in small intervals to allow quick shutdown
                for _ in range(60):  # Check every minute, sleep for 1 second intervals
                    if self.stop_refresh:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Background refresh worker error: {e}")
                time.sleep(60)  # Wait before retrying
    
    def _needs_refresh(self) -> bool:
        """Check if data refresh is needed"""
        if self.last_update is None:
            return True
            
        time_since_update = (datetime.utcnow() - self.last_update).total_seconds() / 60
        return time_since_update >= self.refresh_interval_minutes
    
    def refresh_satellite_data(self, force: bool = False) -> bool:
        """Manually trigger satellite data refresh"""
        if not force and not self._needs_refresh():
            logger.info("Refresh not needed yet")
            return True
            
        try:
            self.last_fetch_attempt = datetime.utcnow()
            
            # Attempt to fetch live data
            categories = ['active_satellites', 'space_stations', 'weather', 'geo']
            new_tle_data = self.fetcher.fetch_multiple_categories(categories, 25)
            
            if new_tle_data:
                self.cached_tle_data = new_tle_data
                self.last_update = datetime.utcnow()
                self.fetch_failure_count = 0
                self.is_demo_mode = False
                logger.info(f"Successfully refreshed {len(new_tle_data)} satellite records")
                return True
            else:
                raise Exception("No data received from Celestrak")
                
        except Exception as e:
            self.fetch_failure_count += 1
            logger.warning(f"Fetch attempt {self.fetch_failure_count} failed: {e}")
            
            # Switch to demo mode after multiple failures
            if self.fetch_failure_count >= self.max_fetch_failures:
                self._enter_demo_mode()
            
            return False
    
    def _enter_demo_mode(self):
        """Enter demo mode with synthetic data"""
        if not self.is_demo_mode:
            logger.warning("Entering demo mode with synthetic satellite data")
            self.is_demo_mode = True
            self.synthetic_satellites = self._generate_synthetic_satellites(50)
            self.last_update = datetime.utcnow()
    
    def get_satellite_data(self, categories: List[str] = None, limit: int = 100) -> List[TLEData]:
        """Get satellite TLE data with fallback to cached or synthetic data"""
        if categories is None:
            categories = ['active_satellites', 'space_stations', 'weather']
            
        try:
            # Attempt to fetch live data
            tle_data = self.fetcher.fetch_multiple_categories(categories, limit // len(categories))
            
            if tle_data:
                self.cached_tle_data = tle_data
                self.last_update = datetime.utcnow()
                return tle_data[:limit]
                
        except Exception as e:
            logger.warning(f"Failed to fetch live TLE data: {e}")
            
        # Fallback to cached data or generate synthetic
        if self.cached_tle_data:
            logger.info("Using cached TLE data")
            return self.cached_tle_data[:limit]
            
        if self.use_synthetic_fallback:
            logger.info("Generating synthetic satellite data")
            return self._generate_synthetic_satellites(limit)
            
        return []
    
    def get_debris_data(self, num_objects: int = 200, include_collision_scenarios: bool = True) -> List[DebrisObject]:
        """Get space debris data with optional collision scenarios"""
        if not self.cached_debris_data or len(self.cached_debris_data) < num_objects:
            logger.info("Generating fresh debris data")
            
            # Generate base debris field
            base_count = int(num_objects * 0.8) if include_collision_scenarios else num_objects
            self.cached_debris_data = self.debris_generator.generate_debris_field(base_count)
            
            # Add collision scenarios for demo
            if include_collision_scenarios:
                collision_count = num_objects - base_count
                satellites = self.get_satellite_data(limit=10)
                collision_debris = self.debris_generator.generate_collision_scenarios(satellites, collision_count)
                self.cached_debris_data.extend(collision_debris)
            
        return self.cached_debris_data[:num_objects]
    
    def _generate_synthetic_satellites(self, count: int) -> List[TLEData]:
        """Generate synthetic satellite TLE data for demo purposes"""
        synthetic_satellites = []
        base_time = datetime.utcnow()
        
        satellite_names = [
            "ISS (ZARYA)", "HUBBLE SPACE TELESCOPE", "STARLINK-1007", 
            "NOAA-19", "GOES-16", "TERRA", "AQUA", "LANDSAT 8",
            "JASON-3", "SENTINEL-1A", "METEOSAT-11", "GPS BIIR-2"
        ]
        
        for i in range(count):
            name = f"{random.choice(satellite_names)}-{i}" if i >= len(satellite_names) else satellite_names[i % len(satellite_names)]
            norad_id = 25544 + i  # Start from ISS NORAD ID
            
            # Generate synthetic TLE lines (simplified)
            line1 = f"1 {norad_id:5d}U 98067A   23001.00000000  .00000000  00000-0  00000-0 0  9999"
            line2 = f"2 {norad_id:5d}  51.6400 000.0000 0000000   0.0000   0.0000 15.50000000000000"
            
            synthetic_satellites.append(TLEData(
                name=name,
                line1=line1,
                line2=line2,
                norad_id=norad_id,
                timestamp=base_time
            ))
            
        return synthetic_satellites
    
    def build_spatial_index(self, objects: List[Union[TLEData, DebrisObject]]) -> Any:
        """Build KD-tree spatial index for efficient collision detection"""
        try:
            from sklearn.neighbors import NearestNeighbors
            
            # Extract 3D positions
            positions = []
            for obj in objects:
                if hasattr(obj, 'position') and obj.position:
                    # DebrisObject has position tuple (x, y, z)
                    positions.append(list(obj.position))
                elif hasattr(obj, 'mean_anomaly'):
                    # For TLE objects without computed positions, use orbital elements as approximation
                    positions.append([obj.mean_anomaly * 1000, obj.inclination * 100, obj.eccentricity * 10000])
            
            if len(positions) < 2:
                return None
                
            nn = NearestNeighbors(n_neighbors=min(10, len(positions)), algorithm='kd_tree')
            nn.fit(positions)
            
            logger.info(f"Built KD-tree spatial index for {len(positions)} objects")
            return nn
            
        except ImportError:
            logger.warning("scikit-learn not available, falling back to brute force collision detection")
            return None
        except Exception as e:
            logger.error(f"Error building spatial index: {e}")
            return None
    
    def find_nearby_objects(self, target_pos: List[float], spatial_index: Any, 
                           all_objects: List[Union[TLEData, DebrisObject]], 
                           threshold_km: float = 5.0) -> List[Tuple[int, float]]:
        """Find objects within threshold distance using spatial index"""
        if spatial_index is None:
            return self._brute_force_proximity_search(target_pos, all_objects, threshold_km)
        
        try:
            distances, indices = spatial_index.kneighbors([target_pos], n_neighbors=min(20, len(all_objects)))
            
            nearby = []
            for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
                # Convert spatial distance back to kilometers (approximate)
                dist_km = dist / 100  # Rough conversion based on our scaling
                if dist_km <= threshold_km:
                    nearby.append((idx, dist_km))
            
            return nearby
            
        except Exception as e:
            logger.error(f"Error in spatial proximity search: {e}")
            return self._brute_force_proximity_search(target_pos, all_objects, threshold_km)
    
    def _brute_force_proximity_search(self, target_pos: List[float], 
                                     all_objects: List[Union[TLEData, DebrisObject]], 
                                     threshold_km: float) -> List[Tuple[int, float]]:
        """Fallback brute force proximity search"""
        nearby = []
        for i, obj in enumerate(all_objects):
            try:
                if hasattr(obj, 'position') and obj.position:
                    obj_pos = list(obj.position)
                else:
                    # Skip objects without computed positions
                    continue
                    
                # Calculate Euclidean distance in kilometers
                dist = sum((a - b) ** 2 for a, b in zip(target_pos, obj_pos)) ** 0.5
                if dist <= threshold_km:
                    nearby.append((i, dist))
            except Exception:
                continue
                
        return nearby
    
    def export_data(self, filepath: str, include_debris: bool = True) -> bool:
        """Export satellite and debris data to JSON file"""
        try:
            export_data = {
                'metadata': {
                    'export_time': datetime.utcnow().isoformat() + 'Z',
                    'data_source': 'live' if not self.is_demo_mode else 'synthetic',
                    'last_update': self.last_update.isoformat() + 'Z' if self.last_update else None,
                    'total_satellites': len(self.cached_tle_data) if self.cached_tle_data else 0,
                    'total_debris': len(self.cached_debris_data) if self.cached_debris_data else 0
                },
                'satellites': [],
                'debris': []
            }
            
            # Export satellite data
            if self.cached_tle_data:
                for sat in self.cached_tle_data:
                    export_data['satellites'].append({
                        'name': sat.name,
                        'norad_id': sat.norad_id,
                        'line1': sat.line1,
                        'line2': sat.line2,
                        'epoch': sat.epoch.isoformat() + 'Z' if hasattr(sat, 'epoch') and sat.epoch else None,
                        'mean_motion': getattr(sat, 'mean_motion', 0.0),
                        'eccentricity': getattr(sat, 'eccentricity', 0.0),
                        'inclination': getattr(sat, 'inclination', 0.0),
                        'ra_of_asc_node': getattr(sat, 'ra_of_asc_node', 0.0),
                        'arg_of_perigee': getattr(sat, 'arg_of_perigee', 0.0),
                        'mean_anomaly': getattr(sat, 'mean_anomaly', 0.0)
                    })
            
            # Export debris data
            if include_debris and self.cached_debris_data:
                for debris in self.cached_debris_data:
                    export_data['debris'].append({
                        'object_id': debris.id,
                        'position': debris.position,
                        'velocity': debris.velocity,
                        'mass': debris.mass,
                        'size': debris.size,
                        'altitude': debris.altitude,
                        'inclination': debris.inclination,
                        'eccentricity': debris.eccentricity,
                        'orbital_regime': debris.orbital_regime,
                        'risk_category': debris.risk_category
                    })
            
            with open(filepath, 'w') as f:
                import json
                json.dump(export_data, f, indent=2)
            
            logger.info(f"Exported data to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return False
    
    def import_data(self, filepath: str, replace_existing: bool = False) -> bool:
        """Import satellite and debris data from JSON file"""
        try:
            with open(filepath, 'r') as f:
                import json
                import_data = json.load(f)
            
            # Validate data structure
            if 'satellites' not in import_data and 'debris' not in import_data:
                logger.error("Invalid data file: missing satellites or debris sections")
                return False
            
            # Import satellites
            if 'satellites' in import_data and import_data['satellites']:
                imported_satellites = []
                for sat_data in import_data['satellites']:
                    try:
                        epoch = None
                        if sat_data.get('epoch'):
                            epoch = datetime.fromisoformat(sat_data['epoch'].replace('Z', '+00:00'))
                        
                        satellite = TLEData(
                            name=sat_data['name'],
                            norad_id=sat_data['norad_id'],
                            line1=sat_data['line1'],
                            line2=sat_data['line2'],
                            epoch=epoch,
                            mean_motion=sat_data.get('mean_motion', 0.0),
                            eccentricity=sat_data.get('eccentricity', 0.0),
                            inclination=sat_data.get('inclination', 0.0),
                            ra_of_asc_node=sat_data.get('ra_of_asc_node', 0.0),
                            arg_of_perigee=sat_data.get('arg_of_perigee', 0.0),
                            mean_anomaly=sat_data.get('mean_anomaly', 0.0)
                        )
                        imported_satellites.append(satellite)
                        
                    except Exception as e:
                        logger.warning(f"Error importing satellite {sat_data.get('name', 'unknown')}: {e}")
                
                if replace_existing or not self.cached_tle_data:
                    self.cached_tle_data = imported_satellites
                else:
                    self.cached_tle_data.extend(imported_satellites)
                
                logger.info(f"Imported {len(imported_satellites)} satellites")
            
            # Import debris (using current DebrisObject structure)
            if 'debris' in import_data and import_data['debris']:
                imported_debris = []
                for debris_data in import_data['debris']:
                    try:
                        debris = DebrisObject(
                            id=debris_data['object_id'],
                            position=tuple(debris_data['position']),
                            velocity=tuple(debris_data['velocity']),
                            mass=debris_data['mass'],
                            size=debris_data['size'],
                            altitude=debris_data.get('altitude', 400.0),
                            inclination=debris_data.get('inclination', 51.6),
                            eccentricity=debris_data.get('eccentricity', 0.0),
                            orbital_regime=debris_data.get('orbital_regime', 'LEO'),
                            risk_category=debris_data.get('risk_category', 'medium'),
                            timestamp=datetime.utcnow()
                        )
                        imported_debris.append(debris)
                        
                    except Exception as e:
                        logger.warning(f"Error importing debris {debris_data.get('object_id', 'unknown')}: {e}")
                
                if replace_existing or not self.cached_debris_data:
                    self.cached_debris_data = imported_debris
                else:
                    self.cached_debris_data.extend(imported_debris)
                
                logger.info(f"Imported {len(imported_debris)} debris objects")
            
            # Update metadata
            if 'metadata' in import_data:
                metadata = import_data['metadata']
                if metadata.get('last_update'):
                    self.last_update = datetime.fromisoformat(metadata['last_update'].replace('Z', '+00:00'))
                if metadata.get('data_source') == 'synthetic':
                    self.is_demo_mode = True
            
            logger.info(f"Successfully imported data from {filepath}")
            return True
            
        except FileNotFoundError:
            logger.error(f"Import file not found: {filepath}")
            return False
        except Exception as e:
            logger.error(f"Error importing data: {e}")
            return False
    
    def get_status_info(self) -> Dict[str, Any]:
        """Get comprehensive status information"""
        return {
            'data_source': 'live' if not self.is_demo_mode else 'synthetic',
            'satellite_count': len(self.cached_tle_data) if self.cached_tle_data else 0,
            'debris_count': len(self.cached_debris_data) if self.cached_debris_data else 0,
            'last_update': self.last_update.isoformat() + 'Z' if self.last_update else None,
            'data_age_minutes': (datetime.utcnow() - self.last_update).total_seconds() / 60 if self.last_update else None,
            'refresh_interval': self.refresh_interval_minutes,
            'fetch_failures': self.fetch_failure_count,
            'auto_refresh_active': self.refresh_thread is not None and self.refresh_thread.is_alive()
        }
    
    def cleanup(self):
        """Clean up resources before shutdown"""
        try:
            self.stop_background_refresh()
            logger.info("DataManager cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def get_data_summary(self) -> Dict:
        """Get summary of available data"""
        return {
            'satellites_count': len(self.cached_tle_data) if self.cached_tle_data else 0,
            'debris_count': len(self.cached_debris_data) if self.cached_debris_data else 0,
            'last_update': self.last_update,
            'data_age_minutes': (datetime.utcnow() - self.last_update).total_seconds() / 60 if self.last_update else None
        }

# Example usage and testing
if __name__ == "__main__":
    # Initialize data manager
    data_manager = DataManager()
    
    # Test satellite data fetching
    logger.info("Testing satellite data fetching...")
    satellites = data_manager.get_satellite_data(limit=20)
    print(f"Retrieved {len(satellites)} satellites")
    
    if satellites:
        print(f"Sample satellite: {satellites[0].name}")
        
    # Test debris generation
    logger.info("Testing debris generation...")
    debris = data_manager.get_debris_data(50)
    print(f"Generated {len(debris)} debris objects")
    
    if debris:
        print(f"Sample debris: {debris[0].id}, size: {debris[0].size:.3f}m")
        
    # Print summary
    summary = data_manager.get_data_summary()
    print(f"Data summary: {summary}")