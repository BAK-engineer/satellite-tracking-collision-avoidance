"""
Live Orbital Ballet - Collision Avoidance Maneuver Planning Module
Automated delta-v maneuver recommendations for collision avoidance
"""

import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
import logging
from scipy.optimize import minimize, differential_evolution
from scipy.integrate import solve_ivp
import math
from enum import Enum

logger = logging.getLogger(__name__)

class ManeuverType(Enum):
    """Types of collision avoidance maneuvers"""
    RADIAL_IN = "radial_inward"          # Decrease altitude
    RADIAL_OUT = "radial_outward"        # Increase altitude  
    TANGENTIAL_PROGRADE = "tangential_prograde"     # Speed up
    TANGENTIAL_RETROGRADE = "tangential_retrograde" # Slow down
    NORMAL_POSITIVE = "normal_positive"   # Out-of-plane positive
    NORMAL_NEGATIVE = "normal_negative"   # Out-of-plane negative
    COMBINED = "combined"                 # Multi-axis maneuver

@dataclass
class ManeuverVector:
    """Represents a delta-v maneuver vector"""
    delta_v_total: float        # Total delta-v magnitude (m/s)
    delta_v_radial: float      # Radial component (m/s)
    delta_v_tangential: float  # Tangential component (m/s)  
    delta_v_normal: float      # Normal component (m/s)
    
    # Execution details
    execution_time: datetime
    burn_duration: float       # seconds
    thrust_direction: Tuple[float, float, float]  # unit vector in ECI
    
    @property
    def delta_v_vector(self) -> np.ndarray:
        """Get delta-v as 3D vector"""
        return np.array([self.delta_v_radial, self.delta_v_tangential, self.delta_v_normal])
    
    @property
    def fuel_cost_kg(self) -> float:
        """Estimate fuel cost using Tsiolkovsky rocket equation"""
        # Assume Isp = 300s for typical satellite thruster
        g0 = 9.81  # m/s²
        isp = 300  # specific impulse
        satellite_mass = 1000  # kg (typical small satellite)
        
        # Delta-v in m/s
        dv = self.delta_v_total
        
        # Mass ratio from rocket equation: exp(dv / (g0 * Isp))
        mass_ratio = np.exp(dv / (g0 * isp))
        fuel_mass = satellite_mass * (mass_ratio - 1)
        
        return fuel_mass

@dataclass  
class AvoidanceStrategy:
    """Complete collision avoidance strategy"""
    primary_maneuver: ManeuverVector
    backup_maneuvers: List[ManeuverVector]
    strategy_type: str
    success_probability: float
    risk_reduction: float
    total_delta_v_cost: float
    implementation_complexity: str  # 'simple', 'moderate', 'complex'
    
    # Timing information
    decision_deadline: datetime
    execution_window_start: datetime
    execution_window_end: datetime
    
    # Safety margins
    minimum_miss_distance: float  # km
    confidence_interval: float    # statistical confidence

class TrajectoryPredictor:
    """Predicts satellite trajectories after maneuvers"""
    
    def __init__(self):
        self.earth_mu = 398600.4418e9  # m³/s² (Earth's gravitational parameter)
        self.earth_radius = 6371000    # m
        
    def predict_trajectory_after_maneuver(self, initial_state: Dict, 
                                        maneuver: ManeuverVector,
                                        prediction_hours: float = 48) -> List[Dict]:
        """
        Predict satellite trajectory after executing a maneuver
        
        Args:
            initial_state: Initial orbital state {position, velocity, timestamp}
            maneuver: Maneuver to execute
            prediction_hours: How far to predict (hours)
            
        Returns:
            List of predicted states over time
        """
        # Convert initial conditions to meters and m/s
        r0 = np.array(initial_state['position']) * 1000  # km to m
        v0 = np.array(initial_state['velocity']) * 1000  # km/s to m/s
        
        # Apply maneuver delta-v at execution time
        maneuver_dv = np.array([
            maneuver.delta_v_radial,
            maneuver.delta_v_tangential, 
            maneuver.delta_v_normal
        ])
        
        # Convert maneuver to ECI frame (simplified)
        v_post_maneuver = v0 + maneuver_dv
        
        # Initial conditions for integration
        y0 = np.concatenate([r0, v_post_maneuver])
        
        # Time span for prediction
        t_span = (0, prediction_hours * 3600)  # seconds
        t_eval = np.linspace(0, prediction_hours * 3600, 
                           int(prediction_hours * 4))  # 15-minute intervals
        
        # Integrate trajectory using two-body dynamics
        sol = solve_ivp(self._orbital_dynamics, t_span, y0, 
                       t_eval=t_eval, rtol=1e-8)
        
        if not sol.success:
            logger.error("Trajectory integration failed")
            return []
        
        # Convert results back to states
        predicted_states = []
        base_time = initial_state['timestamp']
        
        for i, t in enumerate(sol.t):
            position = sol.y[:3, i] / 1000  # m to km
            velocity = sol.y[3:, i] / 1000  # m/s to km/s
            timestamp = base_time + timedelta(seconds=t)
            
            predicted_states.append({
                'position': position.tolist(),
                'velocity': velocity.tolist(),
                'timestamp': timestamp,
                'time_since_maneuver': t / 3600  # hours
            })
        
        return predicted_states
    
    def _orbital_dynamics(self, t: float, y: np.ndarray) -> np.ndarray:
        """
        Two-body orbital dynamics for trajectory integration
        
        Args:
            t: Time (seconds)
            y: State vector [x, y, z, vx, vy, vz] in meters and m/s
            
        Returns:
            Derivative [vx, vy, vz, ax, ay, az]
        """
        r = y[:3]  # Position
        v = y[3:]  # Velocity
        
        # Distance from Earth center
        r_mag = np.linalg.norm(r)
        
        # Gravitational acceleration (two-body)
        a_grav = -self.earth_mu / r_mag**3 * r
        
        # Additional perturbations could be added here:
        # - J2 gravitational harmonics
        # - Atmospheric drag 
        # - Solar radiation pressure
        # - Third-body effects (Moon, Sun)
        
        # For now, just two-body dynamics
        dydt = np.concatenate([v, a_grav])
        
        return dydt

class CollisionAvoidanceOptimizer:
    """Optimizes collision avoidance maneuvers"""
    
    def __init__(self):
        self.trajectory_predictor = TrajectoryPredictor()
        
    def find_optimal_avoidance_maneuver(self, satellite_state: Dict,
                                      threat_object_state: Dict,
                                      collision_time: datetime,
                                      constraints: Dict = None) -> AvoidanceStrategy:
        """
        Find optimal collision avoidance maneuver using optimization
        
        Args:
            satellite_state: Current satellite orbital state
            threat_object_state: Threatening object state
            collision_time: Predicted collision time
            constraints: Maneuver constraints (max delta-v, execution windows)
            
        Returns:
            Optimized avoidance strategy
        """
        if constraints is None:
            constraints = {
                'max_delta_v': 50.0,      # m/s maximum delta-v
                'min_execution_lead_time': 1.0,  # hours before collision
                'max_execution_lead_time': 48.0  # hours before collision
            }
        
        # Define the optimization problem
        def objective_function(maneuver_params):
            """
            Objective function to minimize: weighted combination of:
            - Delta-v cost
            - Collision probability after maneuver
            - Execution complexity
            """
            return self._evaluate_maneuver_cost(
                maneuver_params, satellite_state, threat_object_state, 
                collision_time, constraints
            )
        
        # Optimization bounds: [delta_v_magnitude, direction_theta, direction_phi, execution_time_offset]
        bounds = [
            (0.1, constraints['max_delta_v']),     # Delta-v magnitude (m/s)
            (0, 2 * np.pi),                        # Direction theta (radians)
            (0, np.pi),                            # Direction phi (radians)  
            (constraints['min_execution_lead_time'] * 3600,  # Execution time offset (seconds)
             constraints['max_execution_lead_time'] * 3600)
        ]
        
        # Use differential evolution for global optimization
        result = differential_evolution(
            objective_function, 
            bounds,
            maxiter=100,
            popsize=15,
            seed=42
        )
        
        if not result.success:
            logger.warning("Optimization did not converge, using fallback strategy")
            return self._generate_fallback_strategy(satellite_state, threat_object_state, 
                                                  collision_time)
        
        # Convert optimal parameters to maneuver
        optimal_maneuver = self._params_to_maneuver(
            result.x, satellite_state, collision_time
        )
        
        # Generate complete strategy
        strategy = self._build_avoidance_strategy(
            optimal_maneuver, satellite_state, threat_object_state, 
            collision_time, result.fun
        )
        
        return strategy
    
    def _evaluate_maneuver_cost(self, params: np.ndarray, satellite_state: Dict,
                              threat_state: Dict, collision_time: datetime,
                              constraints: Dict) -> float:
        """Evaluate cost function for a given maneuver"""
        try:
            # Convert parameters to maneuver
            maneuver = self._params_to_maneuver(params, satellite_state, collision_time)
            
            # Predict trajectory after maneuver
            predicted_states = self.trajectory_predictor.predict_trajectory_after_maneuver(
                satellite_state, maneuver, prediction_hours=72
            )
            
            if not predicted_states:
                return 1e6  # High penalty for failed prediction
            
            # Calculate minimum miss distance
            min_miss_distance = self._calculate_minimum_miss_distance(
                predicted_states, threat_state, collision_time
            )
            
            # Cost components
            delta_v_cost = maneuver.delta_v_total / constraints['max_delta_v']  # Normalized
            
            # Miss distance cost (penalty for close approaches)
            miss_distance_cost = max(0, (5.0 - min_miss_distance) / 5.0)  # 5km safety margin
            
            # Execution timing cost (prefer earlier maneuvers)
            time_to_execution = (maneuver.execution_time - datetime.utcnow()).total_seconds() / 3600
            timing_cost = 1.0 / (1.0 + time_to_execution)  # Prefer later execution
            
            # Combined weighted cost
            total_cost = (0.3 * delta_v_cost + 
                         0.6 * miss_distance_cost + 
                         0.1 * timing_cost)
            
            return total_cost
            
        except Exception as e:
            logger.error(f"Error evaluating maneuver cost: {e}")
            return 1e6  # High penalty for errors
    
    def _params_to_maneuver(self, params: np.ndarray, satellite_state: Dict,
                          collision_time: datetime) -> ManeuverVector:
        """Convert optimization parameters to ManeuverVector"""
        delta_v_mag, theta, phi, time_offset = params
        
        # Execution time
        execution_time = collision_time - timedelta(seconds=time_offset)
        
        # Convert spherical coordinates to Cartesian delta-v
        delta_v_x = delta_v_mag * np.sin(phi) * np.cos(theta)
        delta_v_y = delta_v_mag * np.sin(phi) * np.sin(theta) 
        delta_v_z = delta_v_mag * np.cos(phi)
        
        # For simplicity, map to RTN (Radial-Tangential-Normal) frame
        # This is an approximation - real implementation would need proper frame conversion
        delta_v_radial = delta_v_x
        delta_v_tangential = delta_v_y
        delta_v_normal = delta_v_z
        
        # Thrust direction (unit vector)
        thrust_dir = np.array([delta_v_x, delta_v_y, delta_v_z])
        if np.linalg.norm(thrust_dir) > 0:
            thrust_dir = thrust_dir / np.linalg.norm(thrust_dir)
        
        return ManeuverVector(
            delta_v_total=delta_v_mag,
            delta_v_radial=delta_v_radial,
            delta_v_tangential=delta_v_tangential,
            delta_v_normal=delta_v_normal,
            execution_time=execution_time,
            burn_duration=max(1.0, delta_v_mag / 0.1),  # Assume 0.1 m/s² thrust
            thrust_direction=tuple(thrust_dir)
        )
    
    def _calculate_minimum_miss_distance(self, predicted_states: List[Dict],
                                       threat_state: Dict, 
                                       collision_time: datetime) -> float:
        """Calculate minimum miss distance between trajectories"""
        min_distance = float('inf')
        
        # Threat position (assumed static or linearly extrapolated)
        threat_pos = np.array(threat_state['position'])
        threat_vel = np.array(threat_state.get('velocity', [0, 0, 0]))
        
        for state in predicted_states:
            # Time difference from collision time
            dt = (state['timestamp'] - collision_time).total_seconds()
            
            # Extrapolate threat position (simple linear motion)
            threat_pos_at_time = threat_pos + threat_vel * dt / 3600  # Convert hours
            
            # Calculate distance
            sat_pos = np.array(state['position'])
            distance = np.linalg.norm(sat_pos - threat_pos_at_time)
            
            min_distance = min(min_distance, distance)
        
        return min_distance
    
    def _build_avoidance_strategy(self, primary_maneuver: ManeuverVector,
                                satellite_state: Dict, threat_state: Dict,
                                collision_time: datetime, cost: float) -> AvoidanceStrategy:
        """Build complete avoidance strategy with backup options"""
        
        # Generate backup maneuvers (simple alternatives)
        backup_maneuvers = []
        
        # Backup 1: Double the primary maneuver
        backup1 = ManeuverVector(
            delta_v_total=primary_maneuver.delta_v_total * 1.5,
            delta_v_radial=primary_maneuver.delta_v_radial * 1.5,
            delta_v_tangential=primary_maneuver.delta_v_tangential * 1.5,
            delta_v_normal=primary_maneuver.delta_v_normal * 1.5,
            execution_time=primary_maneuver.execution_time - timedelta(hours=1),
            burn_duration=primary_maneuver.burn_duration * 1.5,
            thrust_direction=primary_maneuver.thrust_direction
        )
        backup_maneuvers.append(backup1)
        
        # Backup 2: Opposite direction maneuver
        backup2 = ManeuverVector(
            delta_v_total=primary_maneuver.delta_v_total,
            delta_v_radial=-primary_maneuver.delta_v_radial,
            delta_v_tangential=-primary_maneuver.delta_v_tangential,
            delta_v_normal=-primary_maneuver.delta_v_normal,
            execution_time=primary_maneuver.execution_time - timedelta(hours=2),
            burn_duration=primary_maneuver.burn_duration,
            thrust_direction=tuple(-np.array(primary_maneuver.thrust_direction))
        )
        backup_maneuvers.append(backup2)
        
        # Estimate success probability based on cost
        success_probability = max(0.1, 1.0 - cost)
        
        # Calculate risk reduction
        baseline_collision_prob = 0.8  # Assume high baseline risk
        risk_reduction = baseline_collision_prob * success_probability
        
        return AvoidanceStrategy(
            primary_maneuver=primary_maneuver,
            backup_maneuvers=backup_maneuvers,
            strategy_type="optimized_avoidance",
            success_probability=success_probability,
            risk_reduction=risk_reduction,
            total_delta_v_cost=primary_maneuver.delta_v_total,
            implementation_complexity=self._assess_complexity(primary_maneuver),
            decision_deadline=collision_time - timedelta(hours=6),
            execution_window_start=primary_maneuver.execution_time - timedelta(minutes=30),
            execution_window_end=primary_maneuver.execution_time + timedelta(minutes=30),
            minimum_miss_distance=2.0,  # km target
            confidence_interval=0.95
        )
    
    def _assess_complexity(self, maneuver: ManeuverVector) -> str:
        """Assess implementation complexity of a maneuver"""
        if maneuver.delta_v_total < 1.0:
            return "simple"
        elif maneuver.delta_v_total < 10.0:
            return "moderate"
        else:
            return "complex"
    
    def _generate_fallback_strategy(self, satellite_state: Dict, threat_state: Dict,
                                  collision_time: datetime) -> AvoidanceStrategy:
        """Generate simple fallback strategy when optimization fails"""
        # Simple radial outward maneuver
        fallback_maneuver = ManeuverVector(
            delta_v_total=5.0,  # 5 m/s
            delta_v_radial=5.0,
            delta_v_tangential=0.0,
            delta_v_normal=0.0,
            execution_time=collision_time - timedelta(hours=12),
            burn_duration=50.0,  # seconds
            thrust_direction=(1.0, 0.0, 0.0)
        )
        
        return AvoidanceStrategy(
            primary_maneuver=fallback_maneuver,
            backup_maneuvers=[],
            strategy_type="fallback_radial",
            success_probability=0.6,
            risk_reduction=0.4,
            total_delta_v_cost=5.0,
            implementation_complexity="simple",
            decision_deadline=collision_time - timedelta(hours=18),
            execution_window_start=collision_time - timedelta(hours=12, minutes=30),
            execution_window_end=collision_time - timedelta(hours=11, minutes=30),
            minimum_miss_distance=1.0,
            confidence_interval=0.8
        )

class ManeuverPlanner:
    """High-level interface for maneuver planning and execution"""
    
    def __init__(self):
        self.optimizer = CollisionAvoidanceOptimizer()
        self.trajectory_predictor = TrajectoryPredictor()
        self.planned_maneuvers = {}
        
    def plan_collision_avoidance(self, collision_prediction: Dict, 
                               satellite_state: Dict,
                               constraints: Dict = None) -> AvoidanceStrategy:
        """
        Plan collision avoidance maneuver for a predicted collision
        
        Args:
            collision_prediction: Collision prediction data
            satellite_state: Current satellite state
            constraints: Planning constraints
            
        Returns:
            Planned avoidance strategy
        """
        # Extract threat information
        threat_state = {
            'position': collision_prediction.get('debris_position', [0, 0, 0]),
            'velocity': [0, 0, 0],  # Assume static debris
            'timestamp': collision_prediction['timestamp']
        }
        
        collision_time = collision_prediction['timestamp']
        
        # Plan optimal maneuver
        strategy = self.optimizer.find_optimal_avoidance_maneuver(
            satellite_state, threat_state, collision_time, constraints
        )
        
        # Store planned strategy
        maneuver_id = f"maneuver_{collision_prediction['satellite_id']}_{int(collision_time.timestamp())}"
        self.planned_maneuvers[maneuver_id] = strategy
        
        logger.info(f"Planned avoidance maneuver {maneuver_id}: "
                   f"{strategy.total_delta_v_cost:.2f} m/s delta-v, "
                   f"{strategy.success_probability:.1%} success probability")
        
        return strategy
    
    def evaluate_maneuver_effectiveness(self, strategy: AvoidanceStrategy,
                                      satellite_state: Dict) -> Dict:
        """Evaluate the effectiveness of a planned maneuver"""
        
        # Predict trajectory with maneuver
        post_maneuver_states = self.trajectory_predictor.predict_trajectory_after_maneuver(
            satellite_state, strategy.primary_maneuver, prediction_hours=72
        )
        
        # Predict trajectory without maneuver (baseline)
        no_maneuver = ManeuverVector(
            delta_v_total=0, delta_v_radial=0, delta_v_tangential=0, delta_v_normal=0,
            execution_time=datetime.utcnow(), burn_duration=0,
            thrust_direction=(0, 0, 0)
        )
        
        baseline_states = self.trajectory_predictor.predict_trajectory_after_maneuver(
            satellite_state, no_maneuver, prediction_hours=72
        )
        
        # Compare trajectories
        evaluation = {
            'strategy_id': id(strategy),
            'delta_v_cost': strategy.total_delta_v_cost,
            'fuel_cost_kg': strategy.primary_maneuver.fuel_cost_kg,
            'success_probability': strategy.success_probability,
            'risk_reduction': strategy.risk_reduction,
            'implementation_complexity': strategy.implementation_complexity,
            'execution_timeline': {
                'decision_deadline': strategy.decision_deadline,
                'execution_window': (strategy.execution_window_start, 
                                   strategy.execution_window_end),
                'time_until_execution': (strategy.primary_maneuver.execution_time - 
                                       datetime.utcnow()).total_seconds() / 3600
            },
            'trajectory_comparison': {
                'baseline_states': len(baseline_states),
                'post_maneuver_states': len(post_maneuver_states),
                'altitude_change_km': self._calculate_altitude_change(
                    baseline_states, post_maneuver_states
                )
            }
        }
        
        return evaluation
    
    def _calculate_altitude_change(self, baseline_states: List[Dict],
                                 post_maneuver_states: List[Dict]) -> float:
        """Calculate average altitude change from maneuver"""
        if not baseline_states or not post_maneuver_states:
            return 0.0
        
        earth_radius = 6371.0  # km
        
        # Calculate average altitudes
        baseline_alts = [
            np.linalg.norm(state['position']) - earth_radius 
            for state in baseline_states
        ]
        
        maneuver_alts = [
            np.linalg.norm(state['position']) - earth_radius 
            for state in post_maneuver_states[:len(baseline_alts)]
        ]
        
        avg_baseline = np.mean(baseline_alts)
        avg_maneuver = np.mean(maneuver_alts)
        
        return avg_maneuver - avg_baseline
    
    def get_maneuver_summary(self) -> Dict:
        """Get summary of all planned maneuvers"""
        if not self.planned_maneuvers:
            return {
                'total_maneuvers': 0,
                'total_delta_v_cost': 0,
                'average_success_probability': 0,
                'upcoming_executions': 0
            }
        
        strategies = list(self.planned_maneuvers.values())
        current_time = datetime.utcnow()
        
        upcoming_executions = sum(
            1 for strategy in strategies 
            if strategy.primary_maneuver.execution_time > current_time
        )
        
        return {
            'total_maneuvers': len(strategies),
            'total_delta_v_cost': sum(s.total_delta_v_cost for s in strategies),
            'average_success_probability': np.mean([s.success_probability for s in strategies]),
            'upcoming_executions': upcoming_executions,
            'complexity_distribution': {
                complexity: sum(1 for s in strategies if s.implementation_complexity == complexity)
                for complexity in ['simple', 'moderate', 'complex']
            }
        }

# Example usage and testing
if __name__ == "__main__":
    # Initialize maneuver planner
    planner = ManeuverPlanner()
    
    # Test collision scenario
    satellite_state = {
        'position': [7000, 0, 0],      # km (circular orbit ~629 km altitude)
        'velocity': [0, 7.546, 0],     # km/s (circular velocity)
        'timestamp': datetime.utcnow()
    }
    
    collision_prediction = {
        'timestamp': datetime.utcnow() + timedelta(hours=24),
        'satellite_id': 25544,  # ISS
        'debris_id': 'DEBRIS_001',
        'distance_km': 0.8,
        'collision_probability': 0.15,
        'debris_position': [7000.5, 0.2, 0.1]
    }
    
    # Plan avoidance maneuver
    print("Planning collision avoidance maneuver...")
    strategy = planner.plan_collision_avoidance(collision_prediction, satellite_state)
    
    print(f"Planned Strategy:")
    print(f"  Primary maneuver: {strategy.primary_maneuver.delta_v_total:.2f} m/s")
    print(f"  Success probability: {strategy.success_probability:.1%}")
    print(f"  Execution time: {strategy.primary_maneuver.execution_time}")
    print(f"  Fuel cost: {strategy.primary_maneuver.fuel_cost_kg:.2f} kg")
    
    # Evaluate effectiveness
    evaluation = planner.evaluate_maneuver_effectiveness(strategy, satellite_state)
    print(f"\nManeuver Evaluation:")
    print(f"  Delta-v cost: {evaluation['delta_v_cost']:.2f} m/s")
    print(f"  Risk reduction: {evaluation['risk_reduction']:.1%}")
    print(f"  Complexity: {evaluation['implementation_complexity']}")
    print(f"  Time until execution: {evaluation['execution_timeline']['time_until_execution']:.1f} hours")
    
    # Summary
    summary = planner.get_maneuver_summary()
    print(f"\nManeuver Summary: {summary}")