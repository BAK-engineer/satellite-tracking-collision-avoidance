"""
Live Orbital Ballet - Orbital Mechanics Module
SGP4-based orbit propagation with drift modeling and collision prediction
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
import logging
from sgp4.api import Satrec
from sgp4 import exporter
from sgp4.earth_gravity import wgs84
from sgp4.io import twoline2rv
import math
from scipy.spatial.distance import euclidean
# from astropy import units as u
# from astropy.coordinates import GCRS, CartesianRepresentation
# from astropy.time import Time

logger = logging.getLogger(__name__)

@dataclass
class OrbitalState:
    """Represents the orbital state of an object at a given time"""
    position: Tuple[float, float, float]  # x, y, z in km (ECI coordinates)
    velocity: Tuple[float, float, float]  # vx, vy, vz in km/s
    timestamp: datetime
    object_id: str
    error_flag: bool = False
    
    @property
    def position_vector(self) -> np.ndarray:
        return np.array(self.position)
    
    @property
    def velocity_vector(self) -> np.ndarray:
        return np.array(self.velocity)
    
    @property
    def altitude(self) -> float:
        """Altitude above Earth surface in km"""
        earth_radius = 6371.0
        radius = np.linalg.norm(self.position_vector)
        return radius - earth_radius
    
    @property
    def speed(self) -> float:
        """Orbital speed in km/s"""
        return np.linalg.norm(self.velocity_vector)

@dataclass
class OrbitalElements:
    """Classical orbital elements"""
    semi_major_axis: float      # a (km)
    eccentricity: float         # e (dimensionless)
    inclination: float          # i (radians)
    longitude_ascending: float  # Ω (radians) 
    argument_perigee: float     # ω (radians)
    mean_anomaly: float         # M (radians)
    epoch: datetime
    
    @property
    def period(self) -> float:
        """Orbital period in seconds"""
        mu = 398600.4418  # Earth's gravitational parameter km³/s²
        return 2 * np.pi * np.sqrt(self.semi_major_axis**3 / mu)
    
    @property
    def apogee(self) -> float:
        """Apogee altitude in km"""
        earth_radius = 6371.0
        return self.semi_major_axis * (1 + self.eccentricity) - earth_radius
    
    @property
    def perigee(self) -> float:
        """Perigee altitude in km"""
        earth_radius = 6371.0
        return self.semi_major_axis * (1 - self.eccentricity) - earth_radius

class SGP4Propagator:
    """SGP4 orbital propagator with enhanced error handling"""
    
    def __init__(self):
        self.satellites = {}  # Cache of satellite objects
        self.earth_gravity = wgs84
        
    def load_tle(self, name: str, line1: str, line2: str, norad_id: int) -> bool:
        """
        Load TLE data into SGP4 propagator
        
        Args:
            name: Satellite name
            line1: TLE line 1
            line2: TLE line 2 
            norad_id: NORAD catalog number
            
        Returns:
            Success flag
        """
        try:
            satellite = twoline2rv(line1, line2, self.earth_gravity)
            
            # Check if SGP4 initialization was successful
            if satellite.error != 0:
                logger.warning(f"SGP4 initialization error for {name}: code {satellite.error}")
                return False
                
            self.satellites[norad_id] = {
                'satellite': satellite,
                'name': name,
                'line1': line1,
                'line2': line2
            }
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to load TLE for {name}: {e}")
            return False
    
    def propagate(self, norad_id: int, target_time: datetime) -> Optional[OrbitalState]:
        """
        Propagate satellite to target time using SGP4
        
        Args:
            norad_id: NORAD catalog number
            target_time: Target propagation time
            
        Returns:
            OrbitalState or None if error
        """
        if norad_id not in self.satellites:
            logger.error(f"Satellite {norad_id} not loaded")
            return None
            
        try:
            satellite = self.satellites[norad_id]['satellite']
            
            # Calculate Julian date for SGP4
            jd, fr = self._datetime_to_jd(target_time)
            
            # Propagate using SGP4
            error, position, velocity = satellite.sgp4(jd, fr)
            
            if error != 0:
                logger.warning(f"SGP4 propagation error for {norad_id}: code {error}")
                return OrbitalState(
                    position=(0, 0, 0),
                    velocity=(0, 0, 0),
                    timestamp=target_time,
                    object_id=str(norad_id),
                    error_flag=True
                )
            
            return OrbitalState(
                position=tuple(position),
                velocity=tuple(velocity),
                timestamp=target_time,
                object_id=str(norad_id),
                error_flag=False
            )
            
        except Exception as e:
            logger.error(f"Propagation failed for {norad_id}: {e}")
            return None
    
    def propagate_multiple_times(self, norad_id: int, times: List[datetime]) -> List[OrbitalState]:
        """Propagate satellite to multiple times"""
        states = []
        for time in times:
            state = self.propagate(norad_id, time)
            if state:
                states.append(state)
        return states
    
    def get_orbital_elements(self, norad_id: int) -> Optional[OrbitalElements]:
        """Extract orbital elements from SGP4 satellite"""
        if norad_id not in self.satellites:
            return None
            
        try:
            satellite = self.satellites[norad_id]['satellite']
            
            # Convert SGP4 elements to standard orbital elements
            # Note: SGP4 uses modified elements, this is an approximation
            a = satellite.a * self.earth_gravity.radiusearthkm  # Semi-major axis
            e = satellite.ecco  # Eccentricity
            i = satellite.inclo  # Inclination
            omega = satellite.nodeo  # Longitude of ascending node
            w = satellite.argpo  # Argument of perigee  
            M = satellite.mo  # Mean anomaly
            epoch = satellite.epochdays
            
            # Convert epoch to datetime (simplified)
            year = int(satellite.epochyr)
            if year < 57:
                year += 2000
            else:
                year += 1900
            epoch_dt = datetime(year, 1, 1) + timedelta(days=epoch - 1)
            
            return OrbitalElements(
                semi_major_axis=a,
                eccentricity=e,
                inclination=i,
                longitude_ascending=omega,
                argument_perigee=w,
                mean_anomaly=M,
                epoch=epoch_dt
            )
            
        except Exception as e:
            logger.error(f"Failed to extract orbital elements for {norad_id}: {e}")
            return None
    
    def _datetime_to_jd(self, dt: datetime) -> Tuple[float, float]:
        """Convert datetime to Julian date format for SGP4"""
        # Calculate Julian date manually
        # Julian Day Number calculation
        a = int((14 - dt.month) / 12)
        y = dt.year + 4800 - a
        m = dt.month + 12 * a - 3
        
        jdn = dt.day + int((153 * m + 2) / 5) + 365 * y + int(y / 4) - int(y / 100) + int(y / 400) - 32045
        
        # Add time fraction
        time_frac = (dt.hour + dt.minute / 60.0 + dt.second / 3600.0) / 24.0
        jd = jdn + time_frac - 0.5  # Adjust for noon reference
        
        # Split into integer and fractional parts
        jd_int = int(jd)
        jd_frac = jd - jd_int
        return jd_int, jd_frac

class CollisionAnalyzer:
    """Analyzes potential collisions between space objects"""
    
    def __init__(self, min_distance_threshold: float = 1.0):  # km
        self.min_distance_threshold = min_distance_threshold
        
    def find_close_approaches(self, states1: List[OrbitalState], 
                            states2: List[OrbitalState],
                            time_window_hours: float = 24) -> List[Dict]:
        """
        Find close approaches between two sets of orbital states
        
        Args:
            states1: First set of orbital states (e.g., satellites)
            states2: Second set of orbital states (e.g., debris)
            time_window_hours: Analysis time window
            
        Returns:
            List of close approach events
        """
        close_approaches = []
        
        # Ensure states are time-aligned
        if not states1 or not states2:
            return close_approaches
            
        for state1 in states1:
            for state2 in states2:
                # Only compare states at similar times (within 1 minute)
                time_diff = abs((state1.timestamp - state2.timestamp).total_seconds())
                if time_diff > 60:  # Skip if times are too different
                    continue
                    
                distance = self._calculate_distance(state1, state2)
                
                if distance < self.min_distance_threshold:
                    relative_velocity = self._calculate_relative_velocity(state1, state2)
                    
                    approach_event = {
                        'timestamp': state1.timestamp,
                        'object1_id': state1.object_id,
                        'object2_id': state2.object_id,
                        'distance_km': distance,
                        'relative_velocity_kms': relative_velocity,
                        'collision_probability': self._estimate_collision_probability(
                            distance, relative_velocity
                        ),
                        'risk_level': self._categorize_risk(distance, relative_velocity),
                        'object1_position': state1.position,
                        'object2_position': state2.position,
                        'object1_velocity': state1.velocity,
                        'object2_velocity': state2.velocity
                    }
                    
                    close_approaches.append(approach_event)
        
        # Sort by collision probability (highest first)
        close_approaches.sort(key=lambda x: x['collision_probability'], reverse=True)
        
        return close_approaches
    
    def predict_collision_windows(self, propagator: SGP4Propagator,
                                norad_ids: List[int], 
                                debris_positions: List[Tuple],
                                prediction_hours: float = 168) -> List[Dict]:
        """
        Predict collision windows for multiple satellites over time
        
        Args:
            propagator: SGP4 propagator instance
            norad_ids: List of satellite NORAD IDs
            debris_positions: Static debris positions for analysis
            prediction_hours: Prediction time window (default 7 days)
            
        Returns:
            List of predicted collision events
        """
        collision_predictions = []
        start_time = datetime.utcnow()
        
        # Generate time steps (every hour for next week)
        time_steps = [
            start_time + timedelta(hours=h) 
            for h in np.arange(0, prediction_hours, 1)
        ]
        
        for norad_id in norad_ids:
            # Propagate satellite over time window
            sat_states = propagator.propagate_multiple_times(norad_id, time_steps)
            
            for sat_state in sat_states:
                if sat_state.error_flag:
                    continue
                    
                # Check against all debris positions
                for i, debris_pos in enumerate(debris_positions):
                    debris_state = OrbitalState(
                        position=debris_pos,
                        velocity=(0, 0, 0),  # Assuming static debris
                        timestamp=sat_state.timestamp,
                        object_id=f"DEBRIS_{i}"
                    )
                    
                    distance = self._calculate_distance(sat_state, debris_state)
                    
                    if distance < self.min_distance_threshold * 5:  # Extended threshold
                        collision_prob = self._estimate_collision_probability(
                            distance, sat_state.speed
                        )
                        
                        if collision_prob > 0.01:  # 1% threshold
                            collision_predictions.append({
                                'timestamp': sat_state.timestamp,
                                'satellite_id': norad_id,
                                'debris_id': f"DEBRIS_{i}",
                                'distance_km': distance,
                                'collision_probability': collision_prob,
                                'satellite_position': sat_state.position,
                                'satellite_velocity': sat_state.velocity,
                                'debris_position': debris_pos,
                                'time_to_event_hours': (
                                    sat_state.timestamp - start_time
                                ).total_seconds() / 3600
                            })
        
        return collision_predictions
    
    def _calculate_distance(self, state1: OrbitalState, state2: OrbitalState) -> float:
        """Calculate Euclidean distance between two orbital states"""
        return euclidean(state1.position_vector, state2.position_vector)
    
    def _calculate_relative_velocity(self, state1: OrbitalState, state2: OrbitalState) -> float:
        """Calculate relative velocity magnitude between two objects"""
        rel_vel = state1.velocity_vector - state2.velocity_vector
        return np.linalg.norm(rel_vel)
    
    def _estimate_collision_probability(self, distance: float, relative_velocity: float) -> float:
        """
        Estimate collision probability based on distance and relative velocity
        
        This is a simplified model - real collision probability calculation
        requires detailed shape models and uncertainty propagation
        """
        # Assume effective collision cross-section of 10m radius
        collision_radius = 0.01  # km
        
        if distance <= collision_radius:
            return 1.0
        
        # Probability decreases with distance squared and increases with velocity
        prob = (collision_radius / distance) ** 2
        
        # Velocity factor (higher relative velocity = less time to avoid)
        velocity_factor = min(relative_velocity / 10.0, 2.0)  # Clamp at 2x
        prob *= velocity_factor
        
        return min(prob, 1.0)
    
    def _categorize_risk(self, distance: float, relative_velocity: float) -> str:
        """Categorize collision risk level"""
        prob = self._estimate_collision_probability(distance, relative_velocity)
        
        if prob > 0.1:
            return 'critical'
        elif prob > 0.01:
            return 'high'
        elif prob > 0.001:
            return 'medium'
        else:
            return 'low'

class OrbitPredictionEngine:
    """High-level interface for orbital predictions and collision analysis"""
    
    def __init__(self):
        self.propagator = SGP4Propagator()
        self.collision_analyzer = CollisionAnalyzer()
        self.loaded_satellites = {}
        
    def load_satellite_data(self, tle_data_list: List) -> int:
        """
        Load multiple satellites from TLE data
        
        Args:
            tle_data_list: List of TLEData objects
            
        Returns:
            Number of successfully loaded satellites
        """
        loaded_count = 0
        
        for tle_data in tle_data_list:
            success = self.propagator.load_tle(
                tle_data.name,
                tle_data.line1, 
                tle_data.line2,
                tle_data.norad_id
            )
            
            if success:
                self.loaded_satellites[tle_data.norad_id] = tle_data
                loaded_count += 1
                
        logger.info(f"Loaded {loaded_count}/{len(tle_data_list)} satellites")
        return loaded_count
    
    def get_current_positions(self, norad_ids: Optional[List[int]] = None) -> Dict[int, OrbitalState]:
        """Get current orbital positions for specified satellites"""
        if norad_ids is None:
            norad_ids = list(self.loaded_satellites.keys())
            
        current_time = datetime.utcnow()
        positions = {}
        
        for norad_id in norad_ids:
            state = self.propagator.propagate(norad_id, current_time)
            if state and not state.error_flag:
                positions[norad_id] = state
                
        return positions
    
    def predict_future_positions(self, norad_ids: List[int], 
                               hours_ahead: float = 24,
                               time_step_minutes: float = 60) -> Dict[int, List[OrbitalState]]:
        """Predict future positions for satellites"""
        start_time = datetime.utcnow()
        predictions = {}
        
        # Generate time steps
        num_steps = int(hours_ahead * 60 / time_step_minutes)
        time_steps = [
            start_time + timedelta(minutes=i * time_step_minutes)
            for i in range(num_steps + 1)
        ]
        
        for norad_id in norad_ids:
            states = self.propagator.propagate_multiple_times(norad_id, time_steps)
            # Filter out error states
            valid_states = [state for state in states if not state.error_flag]
            if valid_states:
                predictions[norad_id] = valid_states
                
        return predictions
    
    def analyze_collision_risks(self, satellite_ids: List[int],
                              debris_objects: List,
                              analysis_hours: float = 48) -> Dict:
        """
        Comprehensive collision risk analysis
        
        Args:
            satellite_ids: List of satellite NORAD IDs
            debris_objects: List of debris objects with position data
            analysis_hours: Time window for analysis
            
        Returns:
            Dictionary with collision analysis results
        """
        # Get current and future satellite positions
        future_positions = self.predict_future_positions(
            satellite_ids, 
            hours_ahead=analysis_hours,
            time_step_minutes=30  # 30-minute resolution
        )
        
        # Extract debris positions
        debris_positions = [
            (obj.position[0], obj.position[1], obj.position[2]) 
            for obj in debris_objects
        ]
        
        # Find collision predictions
        collision_predictions = self.collision_analyzer.predict_collision_windows(
            self.propagator,
            satellite_ids,
            debris_positions,
            prediction_hours=analysis_hours
        )
        
        # Analyze risk statistics
        risk_stats = self._analyze_risk_statistics(collision_predictions)
        
        return {
            'predictions': collision_predictions,
            'statistics': risk_stats,
            'satellites_analyzed': len(satellite_ids),
            'debris_objects_analyzed': len(debris_objects),
            'analysis_window_hours': analysis_hours,
            'generated_at': datetime.utcnow()
        }
    
    def _analyze_risk_statistics(self, predictions: List[Dict]) -> Dict:
        """Analyze statistical properties of collision predictions"""
        if not predictions:
            return {
                'total_events': 0,
                'high_risk_events': 0,
                'average_collision_probability': 0,
                'max_collision_probability': 0,
                'events_next_24h': 0
            }
        
        total_events = len(predictions)
        high_risk_events = len([p for p in predictions if p['collision_probability'] > 0.01])
        avg_prob = np.mean([p['collision_probability'] for p in predictions])
        max_prob = max([p['collision_probability'] for p in predictions])
        
        # Count events in next 24 hours
        cutoff_time = datetime.utcnow() + timedelta(hours=24)
        events_24h = len([
            p for p in predictions 
            if p['timestamp'] <= cutoff_time
        ])
        
        return {
            'total_events': total_events,
            'high_risk_events': high_risk_events,
            'average_collision_probability': avg_prob,
            'max_collision_probability': max_prob,
            'events_next_24h': events_24h,
            'risk_distribution': self._calculate_risk_distribution(predictions)
        }
    
    def _calculate_risk_distribution(self, predictions: List[Dict]) -> Dict:
        """Calculate distribution of risk levels"""
        risk_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
        
        for pred in predictions:
            prob = pred['collision_probability']
            if prob > 0.1:
                risk_counts['critical'] += 1
            elif prob > 0.01:
                risk_counts['high'] += 1
            elif prob > 0.001:
                risk_counts['medium'] += 1
            else:
                risk_counts['low'] += 1
                
        return risk_counts

# Example usage and testing
if __name__ == "__main__":
    # Initialize prediction engine
    engine = OrbitPredictionEngine()
    
    # Test with synthetic TLE data
    from data import DataManager
    data_manager = DataManager()
    
    # Get some satellite data
    satellites = data_manager.get_satellite_data(limit=5)
    print(f"Testing with {len(satellites)} satellites")
    
    # Load satellites into prediction engine
    loaded_count = engine.load_satellite_data(satellites)
    print(f"Loaded {loaded_count} satellites successfully")
    
    if loaded_count > 0:
        # Get current positions
        norad_ids = [sat.norad_id for sat in satellites[:3]]
        current_pos = engine.get_current_positions(norad_ids)
        print(f"Current positions for {len(current_pos)} satellites")
        
        # Test collision analysis
        debris = data_manager.get_debris_data(20)
        analysis = engine.analyze_collision_risks(norad_ids, debris, analysis_hours=12)
        print(f"Collision analysis: {analysis['statistics']}")