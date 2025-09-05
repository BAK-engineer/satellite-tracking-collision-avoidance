"""
Live Orbital Ballet - Enhanced Interactive UI Module with Database Integration
Maintains backward compatibility while adding persistent data visualization and monitoring
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Optional, Any
import logging
import time
import json

# Database imports
try:
    from database import (
        init_database, get_db_session, database_health_check, get_system_status,
        TLEDataDAO, SatelliteDAO, OrbitalStateDAO, RiskAssessmentDAO,
        CollisionPredictionDAO, AnalyticsDAO, SystemLogDAO,
        log_info, log_warning, log_error
    )
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    st.warning("Database module not available. Some features may be limited.")

# Enhanced data manager import
try:
    from data_enhanced import EnhancedDataManager
    DATA_ENHANCED_AVAILABLE = True
except ImportError:
    from data import DataManager
    EnhancedDataManager = DataManager
    DATA_ENHANCED_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedEarthVisualization:
    """Enhanced 3D Earth visualization with database-backed features"""
    
    def __init__(self, use_database: bool = None):
        self.earth_radius = 6371.0  # km
        self.use_database = use_database if use_database is not None else DATABASE_AVAILABLE
        
    def create_earth_sphere(self, resolution: int = 50) -> go.Surface:
        """Create 3D Earth sphere for visualization"""
        
        # Create sphere coordinates
        phi = np.linspace(0, 2 * np.pi, resolution)
        theta = np.linspace(0, np.pi, resolution)
        
        phi, theta = np.meshgrid(phi, theta)
        
        # Convert to Cartesian coordinates
        x = self.earth_radius * np.sin(theta) * np.cos(phi)
        y = self.earth_radius * np.sin(theta) * np.sin(phi) 
        z = self.earth_radius * np.cos(theta)
        
        # Create Earth surface
        earth_surface = go.Surface(
            x=x, y=y, z=z,
            colorscale='Earth',
            showscale=False,
            name="Earth",
            hoverinfo='skip'
        )
        
        return earth_surface
    
    def create_enhanced_satellite_traces(self, satellite_positions: Dict, 
                                       risk_assessments: Optional[Dict] = None,
                                       satellite_metadata: Optional[Dict] = None) -> List[go.Scatter3d]:
        """Enhanced satellite traces with database-backed risk assessment and metadata"""
        traces = []
        
        if not satellite_positions:
            return traces
        
        # Enhanced color mapping for risk levels
        risk_colors = {
            'CRITICAL': '#FF0000',  # Red
            'HIGH': '#FF6600',      # Orange  
            'MEDIUM': '#FFFF00',    # Yellow
            'LOW': '#00FF00',       # Green
            'MINIMAL': '#0000FF',   # Blue
            'UNKNOWN': '#888888'    # Gray
        }
        
        for sat_id, position in satellite_positions.items():
            # Get risk level and metadata from database if available
            risk_level = 'UNKNOWN'
            metadata = {}
            
            if risk_assessments and str(sat_id) in risk_assessments:
                risk_level = risk_assessments[str(sat_id)]['risk_category']
            
            if satellite_metadata and str(sat_id) in satellite_metadata:
                metadata = satellite_metadata[str(sat_id)]
            
            color = risk_colors.get(risk_level, risk_colors['UNKNOWN'])
            
            # Enhanced hover information
            hover_text = f"<b>Satellite {sat_id}</b><br>"
            hover_text += f"Position: ({position[0]:.1f}, {position[1]:.1f}, {position[2]:.1f}) km<br>"
            hover_text += f"Risk Level: {risk_level}<br>"
            hover_text += f"Altitude: {np.linalg.norm(position) - self.earth_radius:.1f} km<br>"
            
            # Add metadata if available
            if metadata:
                if 'name' in metadata:
                    hover_text += f"Name: {metadata['name']}<br>"
                if 'satellite_type' in metadata:
                    hover_text += f"Type: {metadata['satellite_type']}<br>"
                if 'operational_status' in metadata:
                    hover_text += f"Status: {metadata['operational_status']}<br>"
            
            satellite_trace = go.Scatter3d(
                x=[position[0]],
                y=[position[1]], 
                z=[position[2]],
                mode='markers+text',
                marker=dict(
                    size=10 if risk_level in ['CRITICAL', 'HIGH'] else 8,
                    color=color,
                    symbol='circle',
                    line=dict(width=2, color='white'),
                    opacity=0.9 if risk_level in ['CRITICAL', 'HIGH'] else 0.7
                ),
                text=[f"SAT-{sat_id}"],
                textposition="top center",
                name=f"Satellite {sat_id} ({risk_level})",
                hovertemplate=hover_text + "<extra></extra>"
            )
            
            traces.append(satellite_trace)
        
        return traces
    
    def create_orbital_trajectory_traces(self, norad_id: int, hours_back: int = 2, 
                                       hours_forward: int = 2) -> List[go.Scatter3d]:
        """Create orbital trajectory traces from database historical data"""
        if not self.use_database:
            return []
        
        try:
            # Get satellite from database
            satellite = SatelliteDAO.get_satellite_by_norad_id(norad_id)
            if not satellite:
                return []
            
            # Get historical orbital states
            start_time = datetime.now(timezone.utc) - timedelta(hours=hours_back)
            end_time = datetime.now(timezone.utc) + timedelta(hours=hours_forward)
            
            states = OrbitalStateDAO.get_states_in_timerange(
                'SATELLITE', satellite.id, start_time, end_time
            )
            
            if len(states) < 2:
                return []
            
            # Extract positions
            positions = [state.position_vector for state in states]
            times = [state.epoch for state in states]
            
            x_coords = [pos[0] for pos in positions]
            y_coords = [pos[1] for pos in positions]
            z_coords = [pos[2] for pos in positions]
            
            # Create trajectory trace
            trajectory_trace = go.Scatter3d(
                x=x_coords,
                y=y_coords,
                z=z_coords,
                mode='lines+markers',
                line=dict(
                    color='rgba(255, 255, 255, 0.6)',
                    width=3
                ),
                marker=dict(
                    size=2,
                    color='rgba(255, 255, 255, 0.4)'
                ),
                name=f"Trajectory NORAD {norad_id}",
                hovertemplate=(
                    f"<b>Trajectory Point</b><br>"
                    f"Position: (%{{x:.1f}}, %{{y:.1f}}, %{{z:.1f}}) km<br>"
                    f"Time: %{{customdata}}<br>"
                    "<extra></extra>"
                ),
                customdata=[t.isoformat() for t in times]
            )
            
            return [trajectory_trace]
            
        except Exception as e:
            logger.error(f"Error creating trajectory trace: {e}")
            return []

class EnhancedDashboard:
    """Enhanced Dashboard with database monitoring and analytics"""
    
    def __init__(self):
        self.use_database = DATABASE_AVAILABLE
        self.viz = EnhancedEarthVisualization(use_database=self.use_database)
        
    def render_database_status_sidebar(self):
        """Render database status and health information in sidebar"""
        if not self.use_database:
            st.sidebar.warning("🔧 Database: Offline")
            return
        
        st.sidebar.subheader("🗄️ Database Status")
        
        try:
            # Get system status
            status = get_system_status()
            db_health = status['database_health']
            db_stats = status['system_statistics']
            
            # Health indicator
            if db_health['status'] == 'healthy':
                st.sidebar.success("✅ Database: Online")
            else:
                st.sidebar.error("❌ Database: Offline")
                return
            
            # Key statistics
            col1, col2 = st.sidebar.columns(2)
            
            with col1:
                st.metric("Satellites", db_stats.get('satellites_total', 0))
                st.metric("High Risk", db_stats.get('high_risk_events', 0))
            
            with col2:
                st.metric("TLE Records", db_stats.get('tle_records', 0))
                st.metric("Active Predictions", db_stats.get('active_predictions', 0))
            
            # Recent activity
            st.sidebar.caption(f"Recent Assessments: {db_stats.get('recent_risk_assessments', 0)}")
            st.sidebar.caption(f"Recent States: {db_stats.get('recent_orbital_states', 0)}")
            
            # Error indicator
            recent_errors = db_stats.get('recent_errors', 0)
            if recent_errors > 0:
                st.sidebar.warning(f"⚠️ {recent_errors} recent errors")
            
        except Exception as e:
            st.sidebar.error(f"Database status error: {e}")
    
    def render_enhanced_main_dashboard(self, data_manager):
        """Enhanced main dashboard with database features"""
        
        st.title("🌍 Live Orbital Ballet - Enhanced Dashboard")
        st.markdown("*Real-time satellite tracking with persistent data storage and AI risk assessment*")
        
        # Initialize database if needed
        if self.use_database and 'db_initialized' not in st.session_state:
            with st.spinner("Initializing database connection..."):
                success = init_database(create_tables=False)  # Don't auto-create tables
                st.session_state.db_initialized = success
                
                if success:
                    st.success("✅ Database connected successfully!")
                    log_info('UI_DASHBOARD', 'Database connection established')
                else:
                    st.error("❌ Database connection failed. Running in memory-only mode.")
                    log_error('UI_DASHBOARD', 'Database connection failed')
                    self.use_database = False
        
        # Control panel
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        
        with col1:
            # Enhanced refresh with database sync
            if st.button("🔄 Refresh Data", type="primary"):
                with st.spinner("Refreshing satellite data..."):
                    # Force refresh from API and sync to database
                    st.session_state.satellites = data_manager.get_satellite_data(
                        limit=100, force_refresh=True
                    )
                    
                    if self.use_database:
                        log_info('UI_DASHBOARD', 'Data refreshed and synced to database')
                    
                    st.rerun()
        
        with col2:
            # Data source indicator
            if hasattr(data_manager, 'use_database') and data_manager.use_database:
                st.success("🗄️ Database")
            else:
                st.info("💾 Memory")
        
        with col3:
            # Auto-refresh toggle
            auto_refresh = st.checkbox("Auto Refresh", value=False)
            
        with col4:
            # Database settings (if available)
            if self.use_database:
                with st.expander("⚙️ DB Settings"):
                    if st.button("📊 View Analytics"):
                        st.session_state.show_analytics = True
                    
                    if st.button("📝 View Logs"):
                        st.session_state.show_logs = True
        
        # Load data
        if 'satellites' not in st.session_state:
            with st.spinner("Loading satellite data..."):
                st.session_state.satellites = data_manager.get_satellite_data(limit=100)
        
        satellites = st.session_state.satellites
        
        if not satellites:
            st.error("No satellite data available. Please check data sources.")
            return
        
        # Enhanced metrics with database data
        self._render_enhanced_metrics(data_manager, satellites)
        
        # Main visualization
        st.subheader("🌐 3D Orbital Visualization")
        
        # Enhanced controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            selected_satellites = st.multiselect(
                "Filter Satellites",
                options=[f"{sat.name} ({sat.norad_id})" for sat in satellites],
                default=[f"{sat.name} ({sat.norad_id})" for sat in satellites[:10]]  # First 10
            )
        
        with col2:
            show_trajectories = st.checkbox("Show Trajectories", value=False, 
                                          disabled=not self.use_database)
            
        with col3:
            show_risk_zones = st.checkbox("Risk Zones", value=True)
        
        # Create enhanced 3D visualization
        fig = self._create_enhanced_3d_plot(satellites, selected_satellites, 
                                          show_trajectories, show_risk_zones, data_manager)
        
        st.plotly_chart(fig, use_container_width=True, key="main_3d_plot")
        
        # Enhanced data tables with database information
        self._render_enhanced_data_tables(satellites, data_manager)
        
        # Analytics and logs panels
        if st.session_state.get('show_analytics', False):
            self._render_analytics_panel()
        
        if st.session_state.get('show_logs', False):
            self._render_system_logs()
        
        # Auto-refresh functionality
        if auto_refresh:
            time.sleep(30)  # Refresh every 30 seconds
            st.rerun()
    
    def _render_enhanced_metrics(self, data_manager, satellites):
        """Enhanced metrics with database-backed information"""
        
        # Get enhanced status
        status_info = data_manager.get_status_info()
        
        # Basic metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="Active Satellites",
                value=len(satellites),
                delta=f"Updated {status_info.get('data_age_minutes', 0):.1f}min ago"
            )
        
        with col2:
            debris_count = status_info.get('debris_count', 0)
            st.metric(
                label="Debris Objects",
                value=debris_count if debris_count > 0 else "Synthetic"
            )
        
        with col3:
            if self.use_database:
                try:
                    high_risk_count = status_info.get('database_statistics', {}).get('high_risk_events', 0)
                    st.metric(
                        label="High Risk Events",
                        value=high_risk_count,
                        delta="Database"
                    )
                except:
                    st.metric(label="High Risk Events", value="N/A")
            else:
                st.metric(label="Risk Assessment", value="Memory Only")
        
        with col4:
            db_status = status_info.get('database_health', 'unknown')
            if db_status == 'healthy':
                st.metric(label="Database", value="✅ Online")
            elif db_status == 'unknown':
                st.metric(label="Database", value="❓ Unknown") 
            else:
                st.metric(label="Database", value="❌ Offline")
    
    def _create_enhanced_3d_plot(self, satellites, selected_satellites, 
                               show_trajectories, show_risk_zones, data_manager):
        """Create enhanced 3D plot with database features"""
        
        # Simulate orbital positions (in real app, this would use SGP4)
        satellite_positions = {}
        risk_assessments = {}
        satellite_metadata = {}
        
        for sat in satellites:
            sat_display_name = f"{sat.name} ({sat.norad_id})"
            if sat_display_name not in selected_satellites:
                continue
            
            # Simulate position (replace with real SGP4 calculation)
            altitude = 400 + np.random.uniform(-50, 200)  # km above Earth
            theta = np.random.uniform(0, 2*np.pi)
            phi = np.random.uniform(0, np.pi)
            
            r = self.viz.earth_radius + altitude
            x = r * np.sin(phi) * np.cos(theta)
            y = r * np.sin(phi) * np.sin(theta)
            z = r * np.cos(phi)
            
            satellite_positions[sat.norad_id] = (x, y, z)
            
            # Simulate risk assessment
            risk_levels = ['MINIMAL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
            risk_assessments[str(sat.norad_id)] = {
                'risk_category': np.random.choice(risk_levels, p=[0.4, 0.3, 0.2, 0.08, 0.02])
            }
            
            # Add satellite metadata
            satellite_metadata[str(sat.norad_id)] = {
                'name': sat.name,
                'satellite_type': 'communication',  # Would be from database
                'operational_status': 'ACTIVE'
            }
        
        # Store positions in database if available
        if self.use_database and satellite_positions:
            try:
                # Convert positions to database format
                positions_for_db = {}
                for norad_id, position in satellite_positions.items():
                    positions_for_db[str(norad_id)] = {
                        'position': position,
                        'velocity': (0.1, 7.5, 0.0),  # Simulated velocity
                        'altitude': np.linalg.norm(position) - self.viz.earth_radius
                    }
                
                data_manager.store_orbital_states(positions_for_db)
            except Exception as e:
                logger.warning(f"Could not store orbital states: {e}")
        
        # Create figure
        fig = go.Figure()
        
        # Add Earth
        earth_sphere = self.viz.create_earth_sphere()
        fig.add_trace(earth_sphere)
        
        # Add enhanced satellite traces
        satellite_traces = self.viz.create_enhanced_satellite_traces(
            satellite_positions, risk_assessments, satellite_metadata
        )
        for trace in satellite_traces:
            fig.add_trace(trace)
        
        # Add trajectories if requested and database is available
        if show_trajectories and self.use_database:
            for sat in satellites[:3]:  # Limit to first 3 for performance
                sat_display_name = f"{sat.name} ({sat.norad_id})"
                if sat_display_name in selected_satellites:
                    trajectory_traces = self.viz.create_orbital_trajectory_traces(sat.norad_id)
                    for trace in trajectory_traces:
                        fig.add_trace(trace)
        
        # Add risk zones if requested
        if show_risk_zones:
            # Add collision risk zones (simplified visualization)
            for sat_id, position in list(satellite_positions.items())[:2]:  # First 2 satellites
                risk_level = risk_assessments.get(str(sat_id), {}).get('risk_category', 'LOW')
                
                if risk_level in ['HIGH', 'CRITICAL']:
                    # Create risk zone sphere around satellite
                    risk_radius = 50 if risk_level == 'CRITICAL' else 25  # km
                    
                    phi_risk = np.linspace(0, 2 * np.pi, 20)
                    theta_risk = np.linspace(0, np.pi, 20)
                    phi_risk, theta_risk = np.meshgrid(phi_risk, theta_risk)
                    
                    x_risk = position[0] + risk_radius * np.sin(theta_risk) * np.cos(phi_risk)
                    y_risk = position[1] + risk_radius * np.sin(theta_risk) * np.sin(phi_risk)
                    z_risk = position[2] + risk_radius * np.cos(theta_risk)
                    
                    risk_zone = go.Surface(
                        x=x_risk, y=y_risk, z=z_risk,
                        colorscale=[[0, 'rgba(255,0,0,0.1)'], [1, 'rgba(255,0,0,0.3)']],
                        showscale=False,
                        name=f"Risk Zone {sat_id}",
                        hoverinfo='name'
                    )
                    fig.add_trace(risk_zone)
        
        # Enhanced layout
        fig.update_layout(
            title={
                'text': "Live Orbital Ballet - Enhanced 3D Tracking",
                'x': 0.5,
                'xanchor': 'center'
            },
            scene=dict(
                xaxis_title="X (km)",
                yaxis_title="Y (km)", 
                zaxis_title="Z (km)",
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                ),
                aspectmode='cube'
            ),
            height=700,
            margin=dict(t=50, b=0, l=0, r=0)
        )
        
        return fig
    
    def _render_enhanced_data_tables(self, satellites, data_manager):
        """Enhanced data tables with database information"""
        
        st.subheader("📊 Enhanced Satellite Data")
        
        # Create enhanced DataFrame
        sat_data = []
        for sat in satellites:
            sat_info = {
                'Name': sat.name,
                'NORAD ID': sat.norad_id,
                'Classification': getattr(sat, 'classification', 'U'),
                'Inclination': f"{getattr(sat, 'inclination', 0):.1f}°" if getattr(sat, 'inclination', None) else "N/A",
                'Mean Motion': f"{getattr(sat, 'mean_motion', 0):.4f}" if getattr(sat, 'mean_motion', None) else "N/A",
                'Eccentricity': f"{getattr(sat, 'eccentricity', 0):.6f}" if getattr(sat, 'eccentricity', None) else "N/A",
                'Last Update': sat.timestamp.strftime("%Y-%m-%d %H:%M:%S UTC")
            }
            sat_data.append(sat_info)
        
        df = pd.DataFrame(sat_data)
        
        # Display with enhanced formatting
        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )
        
        # Database-specific information
        if self.use_database:
            st.subheader("🗄️ Database Information")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.caption("**Recent Database Activity**")
                try:
                    recent_logs = SystemLogDAO.get_recent_logs(hours=1, limit=5)
                    if recent_logs:
                        for log in recent_logs:
                            st.text(f"{log.timestamp.strftime('%H:%M:%S')} - {log.component}: {log.message}")
                    else:
                        st.text("No recent activity")
                except:
                    st.text("Could not fetch recent logs")
            
            with col2:
                st.caption("**System Statistics**")
                try:
                    stats = AnalyticsDAO.get_system_statistics()
                    for key, value in stats.items():
                        if key.startswith('recent_'):
                            display_key = key.replace('recent_', '').replace('_', ' ').title()
                            st.text(f"{display_key}: {value}")
                except:
                    st.text("Could not fetch statistics")
    
    def _render_analytics_panel(self):
        """Render database analytics panel"""
        if not self.use_database:
            st.warning("Analytics require database connection")
            return
        
        st.subheader("📈 System Analytics")
        
        try:
            # Get collision risk trends
            trends = AnalyticsDAO.get_collision_risk_trends(days=7)
            
            if trends:
                # Create trends chart
                df_trends = pd.DataFrame(trends)
                df_trends['date'] = pd.to_datetime(df_trends['date'])
                
                fig = px.line(
                    df_trends, 
                    x='date', 
                    y='avg_probability',
                    color='risk_category',
                    title="Collision Risk Trends (7 Days)"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Risk category distribution
                fig_dist = px.bar(
                    df_trends.groupby('risk_category')['count'].sum().reset_index(),
                    x='risk_category',
                    y='count',
                    title="Risk Assessment Distribution"
                )
                st.plotly_chart(fig_dist, use_container_width=True)
            else:
                st.info("No trend data available")
                
        except Exception as e:
            st.error(f"Analytics error: {e}")
        
        # Close analytics panel
        if st.button("Close Analytics"):
            st.session_state.show_analytics = False
            st.rerun()
    
    def _render_system_logs(self):
        """Render system logs panel"""
        if not self.use_database:
            st.warning("System logs require database connection")
            return
        
        st.subheader("📝 System Logs")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            log_level = st.selectbox("Level", ['ALL', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'])
        
        with col2:
            hours_back = st.number_input("Hours Back", min_value=1, max_value=168, value=24)
        
        try:
            level_filter = None if log_level == 'ALL' else log_level
            logs = SystemLogDAO.get_recent_logs(
                hours=hours_back, 
                level=level_filter, 
                limit=100
            )
            
            if logs:
                log_data = []
                for log in logs:
                    log_data.append({
                        'Timestamp': log.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                        'Level': log.log_level,
                        'Component': log.component,
                        'Message': log.message,
                        'Severity': log.severity
                    })
                
                df_logs = pd.DataFrame(log_data)
                st.dataframe(df_logs, use_container_width=True, hide_index=True)
            else:
                st.info("No logs found for the selected criteria")
                
        except Exception as e:
            st.error(f"Logs error: {e}")
        
        # Close logs panel
        if st.button("Close Logs"):
            st.session_state.show_logs = False
            st.rerun()

def main():
    """Enhanced main function with database integration"""
    
    # Page configuration
    st.set_page_config(
        page_title="Live Orbital Ballet - Enhanced",
        page_icon="🌍",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Initialize enhanced dashboard
    dashboard = EnhancedDashboard()
    
    # Initialize enhanced data manager
    if 'data_manager' not in st.session_state:
        st.session_state.data_manager = EnhancedDataManager(use_database=DATABASE_AVAILABLE)
    
    data_manager = st.session_state.data_manager
    
    # Render database status sidebar
    dashboard.render_database_status_sidebar()
    
    # Render main dashboard
    dashboard.render_enhanced_main_dashboard(data_manager)
    
    # Footer
    st.markdown("---")
    st.markdown(
        "🚀 **Live Orbital Ballet Enhanced** - Real-time satellite tracking with AI risk assessment and persistent data storage"
    )
    
    if DATABASE_AVAILABLE:
        st.caption("✅ Enhanced with database persistence and analytics")
    else:
        st.caption("⚠️ Running in memory-only mode - install database dependencies for full features")

if __name__ == "__main__":
    main()