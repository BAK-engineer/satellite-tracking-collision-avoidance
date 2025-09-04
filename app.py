"""
Live Orbital Ballet - Main Application
Main integration and workflow orchestration with time simulation controls
"""

import streamlit as st
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import time
import threading
from dataclasses import asdict
import traceback

# Import project modules
from data import DataManager, TLEData, DebrisObject
from orbit import OrbitPredictionEngine, OrbitalState
from ai import HybridRiskAssessment, extract_risk_features
from maneuver import ManeuverPlanner
from ui import DashboardComponents, AdvancedVisualizations, create_sidebar_controls, display_header

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class OrbitSimulationState:
    """Manages the state of orbital simulation"""
    
    def __init__(self):
        self.current_time = datetime.utcnow()
        self.simulation_speed = 1.0  # Real-time multiplier
        self.is_running = False
        self.last_update = datetime.utcnow()
        self.time_step_seconds = 60  # Update every minute by default
        self.prediction_window_hours = 24
        
    def advance_time(self, seconds: float):
        """Advance simulation time"""
        self.current_time += timedelta(seconds=seconds)
        self.last_update = datetime.utcnow()
        
    def reset_time(self):
        """Reset simulation to current real time"""
        self.current_time = datetime.utcnow()
        self.last_update = datetime.utcnow()

class LiveOrbitBalletApp:
    """Main application class orchestrating all components"""
    
    def __init__(self):
        self.data_manager = DataManager(use_synthetic_fallback=True)
        self.orbit_engine = OrbitPredictionEngine() 
        self.risk_assessor = HybridRiskAssessment(use_pretrained=True)
        self.maneuver_planner = ManeuverPlanner()
        self.dashboard = DashboardComponents()
        self.advanced_viz = AdvancedVisualizations()
        
        # Application state
        self.simulation_state = OrbitSimulationState()
        self.cached_data = {
            'satellites': [],
            'debris': [],
            'risk_analysis': {},
            'maneuver_plans': {},
            'system_status': {}
        }
        self.last_data_refresh = None
        
        # Performance tracking
        self.performance_metrics = {
            'update_count': 0,
            'average_update_time': 0,
            'last_update_duration': 0
        }
        
    def initialize_system(self):
        """Initialize the orbital tracking system"""
        logger.info("Initializing Live Orbital Ballet system...")
        
        try:
            # Load initial satellite data
            logger.info("Loading satellite TLE data...")
            satellites = self.data_manager.get_satellite_data(
                categories=['active_satellites', 'space_stations', 'weather'],
                limit=50
            )
            
            if satellites:
                # Load into orbit engine
                loaded_count = self.orbit_engine.load_satellite_data(satellites)
                logger.info(f"Loaded {loaded_count} satellites into orbit engine")
                self.cached_data['satellites'] = satellites
            else:
                logger.warning("No satellite data loaded - using demo mode")
                
            # Generate debris field
            logger.info("Generating space debris field...")
            debris = self.data_manager.get_debris_data(200)
            self.cached_data['debris'] = debris
            logger.info(f"Generated {len(debris)} debris objects")
            
            # Initialize system status
            self.cached_data['system_status'] = {
                'satellites_loaded': len(satellites) if satellites else 0,
                'debris_objects': len(debris),
                'system_health': 'Healthy',
                'last_update': datetime.utcnow(),
                'data_age_minutes': 0,
                'update_rate_hz': 0,
                'objects_tracked': (len(satellites) if satellites else 0) + len(debris)
            }
            
            self.last_data_refresh = datetime.utcnow()
            logger.info("System initialization completed successfully")
            
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            st.error(f"System initialization error: {e}")
            self.cached_data['system_status'] = {
                'system_health': 'Error',
                'error_message': str(e)
            }
    
    def update_orbital_positions(self) -> Dict:
        """Update current orbital positions for all tracked objects"""
        start_time = time.time()
        
        try:
            current_positions = {}
            
            if self.cached_data['satellites']:
                # Get current satellite positions
                satellite_ids = [sat.norad_id for sat in self.cached_data['satellites'][:20]]  # Limit for performance
                positions = self.orbit_engine.get_current_positions(satellite_ids)
                
                for norad_id, orbital_state in positions.items():
                    if not orbital_state.error_flag:
                        current_positions[norad_id] = orbital_state.position
            
            # Update performance metrics
            update_duration = time.time() - start_time
            self.performance_metrics['last_update_duration'] = update_duration
            self.performance_metrics['update_count'] += 1
            
            # Calculate running average
            if self.performance_metrics['update_count'] > 1:
                prev_avg = self.performance_metrics['average_update_time']
                count = self.performance_metrics['update_count']
                self.performance_metrics['average_update_time'] = (
                    (prev_avg * (count - 1) + update_duration) / count
                )
            else:
                self.performance_metrics['average_update_time'] = update_duration
            
            logger.debug(f"Updated {len(current_positions)} satellite positions in {update_duration:.3f}s")
            return current_positions
            
        except Exception as e:
            logger.error(f"Error updating orbital positions: {e}")
            return {}
    
    def perform_collision_analysis(self, satellite_positions: Dict) -> Dict:
        """Perform comprehensive collision risk analysis"""
        try:
            if not satellite_positions or not self.cached_data['debris']:
                return {'predictions': [], 'statistics': {}}
            
            # Get satellite IDs and debris data
            satellite_ids = list(satellite_positions.keys())
            debris_objects = self.cached_data['debris'][:100]  # Limit for performance
            
            # Perform collision analysis
            analysis_result = self.orbit_engine.analyze_collision_risks(
                satellite_ids,
                debris_objects,
                analysis_hours=self.simulation_state.prediction_window_hours
            )
            
            # Enhance with AI risk assessment
            enhanced_predictions = []
            for prediction in analysis_result['predictions']:
                try:
                    # Get satellite orbital state
                    sat_id = prediction['satellite_id']
                    if sat_id in satellite_positions:
                        sat_state = OrbitalState(
                            position=prediction['satellite_position'],
                            velocity=prediction['satellite_velocity'],
                            timestamp=prediction['timestamp'],
                            object_id=str(sat_id)
                        )
                        
                        # Create debris state  
                        debris_state = OrbitalState(
                            position=prediction['debris_position'],
                            velocity=(0, 0, 0),  # Assume static
                            timestamp=prediction['timestamp'],
                            object_id=prediction['debris_id']
                        )
                        
                        # Extract features for AI assessment
                        features = extract_risk_features(sat_state, debris_state)
                        
                        # Get AI risk assessment
                        ai_assessment = self.risk_assessor.assess_collision_risk(features)
                        
                        # Enhance prediction with AI results
                        prediction['ai_risk_score'] = ai_assessment['hybrid_risk_score']
                        prediction['ai_risk_category'] = ai_assessment['risk_category']
                        prediction['ai_confidence'] = ai_assessment['confidence']
                        
                        enhanced_predictions.append(prediction)
                        
                except Exception as e:
                    logger.warning(f"Error in AI risk assessment: {e}")
                    enhanced_predictions.append(prediction)  # Keep original prediction
            
            analysis_result['predictions'] = enhanced_predictions
            logger.info(f"Completed collision analysis: {len(enhanced_predictions)} predictions")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error in collision analysis: {e}")
            return {'predictions': [], 'statistics': {}}
    
    def plan_avoidance_maneuvers(self, collision_predictions: List[Dict]) -> Dict:
        """Plan collision avoidance maneuvers for high-risk events"""
        try:
            maneuver_plans = {}
            
            # Filter high-risk predictions
            high_risk_predictions = [
                pred for pred in collision_predictions 
                if pred.get('collision_probability', 0) > 0.01  # 1% threshold
            ]
            
            for prediction in high_risk_predictions[:5]:  # Limit to top 5 for performance
                try:
                    satellite_id = prediction['satellite_id']
                    
                    # Create satellite state for maneuver planning
                    satellite_state = {
                        'position': prediction['satellite_position'],
                        'velocity': prediction['satellite_velocity'], 
                        'timestamp': prediction['timestamp']
                    }
                    
                    # Plan avoidance maneuver
                    strategy = self.maneuver_planner.plan_collision_avoidance(
                        prediction, satellite_state
                    )
                    
                    # Evaluate maneuver effectiveness
                    evaluation = self.maneuver_planner.evaluate_maneuver_effectiveness(
                        strategy, satellite_state
                    )
                    
                    maneuver_plans[satellite_id] = {
                        'strategy': strategy,
                        'evaluation': evaluation,
                        'prediction': prediction
                    }
                    
                except Exception as e:
                    logger.warning(f"Error planning maneuver for satellite {prediction.get('satellite_id')}: {e}")
                    continue
            
            # Get overall maneuver summary
            summary = self.maneuver_planner.get_maneuver_summary()
            
            logger.info(f"Planned {len(maneuver_plans)} avoidance maneuvers")
            
            return {
                'individual_plans': maneuver_plans,
                'summary': summary
            }
            
        except Exception as e:
            logger.error(f"Error in maneuver planning: {e}")
            return {'individual_plans': {}, 'summary': {}}
    
    def update_system_status(self):
        """Update system status and performance metrics"""
        try:
            current_time = datetime.utcnow()
            
            # Calculate data age
            data_age_minutes = 0
            if self.last_data_refresh:
                data_age_minutes = (current_time - self.last_data_refresh).total_seconds() / 60
            
            # Calculate update rate
            update_rate = 0
            if self.performance_metrics['average_update_time'] > 0:
                update_rate = 1.0 / self.performance_metrics['average_update_time']
            
            # Determine system health
            system_health = 'Healthy'
            if data_age_minutes > 30:  # Data older than 30 minutes
                system_health = 'Warning'
            if data_age_minutes > 120:  # Data older than 2 hours
                system_health = 'Error'
            
            self.cached_data['system_status'].update({
                'last_update': current_time,
                'data_age_minutes': data_age_minutes,
                'update_rate_hz': update_rate,
                'system_health': system_health,
                'performance': {
                    'update_count': self.performance_metrics['update_count'],
                    'average_update_time': self.performance_metrics['average_update_time'],
                    'last_update_duration': self.performance_metrics['last_update_duration']
                }
            })
            
        except Exception as e:
            logger.error(f"Error updating system status: {e}")
    
    def run_update_cycle(self) -> Tuple[Dict, Dict, Dict]:
        """Run one complete update cycle and return all data"""
        logger.debug("Running update cycle...")
        
        try:
            # Update orbital positions
            satellite_positions = self.update_orbital_positions()
            
            # Perform collision analysis
            risk_analysis = self.perform_collision_analysis(satellite_positions)
            
            # Plan maneuvers if needed
            maneuver_plans = {}
            if risk_analysis.get('predictions'):
                maneuver_plans = self.plan_avoidance_maneuvers(risk_analysis['predictions'])
            
            # Update system status
            self.update_system_status()
            
            # Cache results
            self.cached_data.update({
                'current_positions': satellite_positions,
                'risk_analysis': risk_analysis,
                'maneuver_plans': maneuver_plans
            })
            
            return satellite_positions, risk_analysis, maneuver_plans
            
        except Exception as e:
            logger.error(f"Error in update cycle: {e}")
            st.error(f"Update cycle error: {e}")
            return {}, {}, {}

def main():
    """Main Streamlit application entry point"""
    
    # Configure Streamlit page
    st.set_page_config(
        page_title="Live Orbital Ballet",
        page_icon="🛰️", 
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize session state
    if 'app_initialized' not in st.session_state:
        st.session_state.app_initialized = False
        st.session_state.app_instance = None
        st.session_state.last_update = None
        st.session_state.auto_refresh = True
    
    # Display header
    display_header()
    
    # Initialize application
    if not st.session_state.app_initialized:
        with st.spinner("🚀 Initializing Live Orbital Ballet system..."):
            try:
                st.session_state.app_instance = LiveOrbitBalletApp()
                st.session_state.app_instance.initialize_system()
                st.session_state.app_initialized = True
                st.success("✅ System initialized successfully!")
                time.sleep(1)  # Brief pause to show success message
            except Exception as e:
                st.error(f"❌ Initialization failed: {e}")
                st.stop()
    
    app = st.session_state.app_instance
    
    # Create sidebar controls
    controls = create_sidebar_controls()
    
    # Update simulation parameters from controls
    app.simulation_state.prediction_window_hours = controls.get('prediction_hours', 24)
    
    # Auto-refresh logic
    placeholder = st.empty()
    
    # Manual refresh button
    col1, col2, col3 = st.columns([1, 1, 4])
    with col1:
        if st.button("🔄 Refresh Now"):
            st.session_state.force_update = True
    
    with col2:
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=controls.get('auto_update', True))
        st.session_state.auto_refresh = auto_refresh
    
    # Determine if update is needed
    should_update = False
    
    if st.session_state.get('force_update', False):
        should_update = True
        st.session_state.force_update = False
    elif auto_refresh and st.session_state.last_update:
        time_since_update = (datetime.utcnow() - st.session_state.last_update).total_seconds()
        should_update = time_since_update >= 30  # 30 second auto-refresh
    elif not st.session_state.last_update:
        should_update = True
    
    # Run update cycle if needed
    if should_update:
        with st.spinner("🛰️ Updating orbital data..."):
            satellite_positions, risk_analysis, maneuver_plans = app.run_update_cycle()
            st.session_state.last_update = datetime.utcnow()
    else:
        # Use cached data
        satellite_positions = app.cached_data.get('current_positions', {})
        risk_analysis = app.cached_data.get('risk_analysis', {})
        maneuver_plans = app.cached_data.get('maneuver_plans', {})
    
    # Create main dashboard layout
    with placeholder.container():
        # Main visualization row
        col1, col2 = st.columns([3, 1])
        
        with col1:
            # Create 3D Earth visualization
            try:
                # Extract risk levels for color coding
                risk_levels = {}
                if risk_analysis.get('predictions'):
                    for pred in risk_analysis['predictions']:
                        sat_id = pred.get('satellite_id')
                        risk_category = pred.get('ai_risk_category', 'LOW')
                        if sat_id:
                            risk_levels[sat_id] = risk_category
                
                # Create main 3D plot
                fig_3d = app.dashboard.create_main_3d_plot(
                    satellite_positions, 
                    app.cached_data.get('debris', [])[:controls.get('max_debris', 200)],
                    risk_assessments=risk_levels
                )
                
                st.plotly_chart(fig_3d, use_container_width=True, key="main_3d_plot")
                
            except Exception as e:
                logger.error(f"Error creating 3D visualization: {e}")
                st.error(f"Visualization error: {e}")
        
        with col2:
            # Risk assessment panel
            app.dashboard.create_risk_assessment_panel(risk_analysis)
            
            # Maneuver planning panel
            maneuver_summary = maneuver_plans.get('summary', {})
            app.dashboard.create_maneuver_planning_panel(maneuver_summary)
        
        # Time simulation controls
        st.markdown("---")
        time_controls = app.dashboard.create_time_simulation_controls()
        
        # Information panels row
        col3, col4 = st.columns(2)
        
        with col3:
            # Satellite information panel
            app.dashboard.create_satellite_info_panel(satellite_positions)
        
        with col4:
            # System status panel
            app.dashboard.create_system_status_panel(app.cached_data.get('system_status', {}))
        
        # Advanced visualizations (expandable)
        with st.expander("📊 Advanced Analytics", expanded=False):
            
            col5, col6 = st.columns(2)
            
            with col5:
                # Orbital elements analysis
                try:
                    orbital_chart = app.advanced_viz.create_orbital_elements_chart(satellite_positions)
                    st.plotly_chart(orbital_chart, use_container_width=True)
                except Exception as e:
                    st.error(f"Orbital elements chart error: {e}")
            
            with col6:
                # Collision timeline
                try:
                    predictions = risk_analysis.get('predictions', [])
                    timeline_chart = app.advanced_viz.create_collision_timeline_chart(predictions)
                    st.plotly_chart(timeline_chart, use_container_width=True)
                except Exception as e:
                    st.error(f"Timeline chart error: {e}")
        
        # Debug information (only in development)
        if st.checkbox("Show Debug Info", value=False):
            st.subheader("🔧 Debug Information")
            
            col7, col8 = st.columns(2)
            
            with col7:
                st.write("**Performance Metrics:**")
                st.json(app.performance_metrics)
                
                st.write("**System Status:**")
                st.json(app.cached_data.get('system_status', {}))
            
            with col8:
                st.write("**Data Summary:**")
                summary = {
                    'satellites_loaded': len(app.cached_data.get('satellites', [])),
                    'debris_objects': len(app.cached_data.get('debris', [])),
                    'current_positions': len(satellite_positions),
                    'risk_predictions': len(risk_analysis.get('predictions', [])),
                    'planned_maneuvers': len(maneuver_plans.get('individual_plans', {}))
                }
                st.json(summary)
    
    # Auto-refresh mechanism
    if auto_refresh:
        time.sleep(1)  # Small delay to prevent excessive CPU usage
        st.rerun()

if __name__ == "__main__":
    main()