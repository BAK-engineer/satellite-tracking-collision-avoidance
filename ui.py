"""
Live Orbital Ballet - Interactive UI Module
Interactive 3D dashboard with Streamlit + Plotly for real-time visualization
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from datetime import datetime
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EarthVisualization:
    """3D Earth visualization with satellites and debris"""
    
    def __init__(self):
        self.earth_radius = 6371.0  # km
        self.earth_texture_url = "https://raw.githubusercontent.com/plotly/datasets/master/2014_world_gdp_with_codes.csv"
        
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
    
    def create_satellite_traces(self, satellite_positions: Dict, 
                              risk_levels: Dict = None) -> List[go.Scatter3d]:
        """Create 3D scatter traces for satellites with risk color coding"""
        traces = []
        
        if not satellite_positions:
            return traces
        
        # Color mapping for risk levels
        risk_colors = {
            'CRITICAL': '#FF0000',  # Red
            'HIGH': '#FF6600',      # Orange  
            'MEDIUM': '#FFFF00',    # Yellow
            'LOW': '#00FF00',       # Green
            'MINIMAL': '#0000FF'    # Blue
        }
        
        default_color = '#888888'  # Gray for unknown risk
        
        for sat_id, position in satellite_positions.items():
            risk_level = risk_levels.get(sat_id, 'UNKNOWN') if risk_levels else 'UNKNOWN'
            color = risk_colors.get(risk_level, default_color)
            
            satellite_trace = go.Scatter3d(
                x=[position[0]],
                y=[position[1]], 
                z=[position[2]],
                mode='markers+text',
                marker=dict(
                    size=8,
                    color=color,
                    symbol='circle',
                    line=dict(width=2, color='white')
                ),
                text=[f"SAT-{sat_id}"],
                textposition="top center",
                name=f"Satellite {sat_id} ({risk_level})",
                hovertemplate=(
                    f"<b>Satellite {sat_id}</b><br>"
                    f"Position: ({position[0]:.1f}, {position[1]:.1f}, {position[2]:.1f}) km<br>"
                    f"Risk Level: {risk_level}<br>"
                    f"Altitude: {np.linalg.norm(position) - self.earth_radius:.1f} km"
                    "<extra></extra>"
                )
            )
            
            traces.append(satellite_trace)
        
        return traces
    
    def create_debris_traces(self, debris_objects: List, 
                           max_display: int = 500) -> List[go.Scatter3d]:
        """Create 3D scatter traces for space debris"""
        traces = []
        
        if not debris_objects:
            return traces
        
        # Limit number of debris objects for performance
        display_debris = debris_objects[:max_display]
        
        # Group debris by risk category for efficient plotting
        debris_by_risk = {'high': [], 'medium': [], 'low': []}
        
        for debris in display_debris:
            risk_cat = getattr(debris, 'risk_category', 'low')
            if risk_cat in debris_by_risk:
                debris_by_risk[risk_cat].append(debris)
            else:
                debris_by_risk['low'].append(debris)
        
        # Color and size mapping for debris risk
        debris_colors = {
            'high': '#FF4444',    # Light red
            'medium': '#FFAA44',  # Orange
            'low': '#CCCCCC'      # Light gray
        }
        
        debris_sizes = {
            'high': 6,
            'medium': 4,
            'low': 2
        }
        
        for risk_cat, debris_list in debris_by_risk.items():
            if not debris_list:
                continue
                
            positions = [obj.position for obj in debris_list]
            sizes = [getattr(obj, 'size', 1.0) for obj in debris_list]
            
            if positions:
                x_coords = [pos[0] for pos in positions]
                y_coords = [pos[1] for pos in positions]
                z_coords = [pos[2] for pos in positions]
                
                debris_trace = go.Scatter3d(
                    x=x_coords,
                    y=y_coords,
                    z=z_coords,
                    mode='markers',
                    marker=dict(
                        size=debris_sizes[risk_cat],
                        color=debris_colors[risk_cat],
                        symbol='circle',
                        opacity=0.6
                    ),
                    name=f"Debris ({risk_cat.title()} Risk)",
                    hovertemplate=(
                        f"<b>Space Debris</b><br>"
                        f"Risk: {risk_cat.title()}<br>"
                        f"Size: %{{customdata:.3f}} m<br>"
                        f"Position: (%{{x:.1f}}, %{{y:.1f}}, %{{z:.1f}}) km"
                        "<extra></extra>"
                    ),
                    customdata=sizes
                )
                
                traces.append(debris_trace)
        
        return traces
    
    def create_orbital_trajectory(self, predicted_states: List[Dict],
                                object_name: str = "Object") -> go.Scatter3d:
        """Create trajectory line for predicted orbital path"""
        if not predicted_states:
            return None
        
        x_coords = [state['position'][0] for state in predicted_states]
        y_coords = [state['position'][1] for state in predicted_states]
        z_coords = [state['position'][2] for state in predicted_states]
        
        trajectory_trace = go.Scatter3d(
            x=x_coords,
            y=y_coords,
            z=z_coords,
            mode='lines+markers',
            line=dict(
                color='cyan',
                width=3
            ),
            marker=dict(
                size=2,
                color='cyan'
            ),
            name=f"{object_name} Trajectory",
            hovertemplate=(
                f"<b>{object_name} Trajectory</b><br>"
                f"Position: (%{{x:.1f}}, %{{y:.1f}}, %{{z:.1f}}) km<br>"
                f"Time: %{{customdata}}<br>"
                "<extra></extra>"
            ),
            customdata=[state.get('timestamp', 'Unknown') for state in predicted_states]
        )
        
        return trajectory_trace

class DashboardComponents:
    """Streamlit dashboard components and widgets"""
    
    def __init__(self):
        self.earth_viz = EarthVisualization()
        
    def create_main_3d_plot(self, satellite_data: Dict, debris_data: List,
                          trajectories: Dict = None, 
                          risk_assessments: Dict = None) -> go.Figure:
        """Create main 3D visualization plot"""
        
        fig = go.Figure()
        
        # Add Earth
        earth_surface = self.earth_viz.create_earth_sphere()
        fig.add_trace(earth_surface)
        
        # Add satellites
        satellite_traces = self.earth_viz.create_satellite_traces(
            satellite_data, risk_assessments
        )
        for trace in satellite_traces:
            fig.add_trace(trace)
        
        # Add debris
        debris_traces = self.earth_viz.create_debris_traces(debris_data)
        for trace in debris_traces:
            fig.add_trace(trace)
        
        # Add trajectories if provided
        if trajectories:
            for obj_name, states in trajectories.items():
                traj_trace = self.earth_viz.create_orbital_trajectory(states, obj_name)
                if traj_trace:
                    fig.add_trace(traj_trace)
        
        # Update layout for 3D scene
        fig.update_layout(
            title="Live Orbital Ballet - Satellite Tracking System",
            scene=dict(
                xaxis=dict(title="X (km)", range=[-15000, 15000]),
                yaxis=dict(title="Y (km)", range=[-15000, 15000]),
                zaxis=dict(title="Z (km)", range=[-15000, 15000]),
                bgcolor="black",
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=0.7)
                )
            ),
            paper_bgcolor="black",
            plot_bgcolor="black",
            font=dict(color="white"),
            height=800,
            showlegend=True,
            legend=dict(
                x=0.02,
                y=0.98,
                bgcolor="rgba(0,0,0,0.8)",
                bordercolor="white",
                borderwidth=1
            )
        )
        
        return fig
    
    def create_risk_assessment_panel(self, risk_data: Dict) -> None:
        """Create risk assessment information panel"""
        
        st.subheader("🚨 Collision Risk Assessment")
        
        if not risk_data:
            st.info("No active collision risks detected")
            return
        
        # Risk statistics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_events = risk_data.get('statistics', {}).get('total_events', 0)
            st.metric("Total Risk Events", total_events)
        
        with col2:
            high_risk = risk_data.get('statistics', {}).get('high_risk_events', 0)
            st.metric("High Risk Events", high_risk, delta=None)
        
        with col3:
            max_prob = risk_data.get('statistics', {}).get('max_collision_probability', 0)
            st.metric("Max Collision Prob", f"{max_prob:.1%}")
        
        with col4:
            events_24h = risk_data.get('statistics', {}).get('events_next_24h', 0)
            st.metric("Events Next 24h", events_24h)
        
        # Risk distribution chart
        if 'statistics' in risk_data and 'risk_distribution' in risk_data['statistics']:
            risk_dist = risk_data['statistics']['risk_distribution']
            
            fig_risk = px.bar(
                x=list(risk_dist.keys()),
                y=list(risk_dist.values()),
                title="Risk Level Distribution",
                color=list(risk_dist.keys()),
                color_discrete_map={
                    'low': 'green',
                    'medium': 'yellow', 
                    'high': 'orange',
                    'critical': 'red'
                }
            )
            fig_risk.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig_risk, use_container_width=True)
    
    def create_maneuver_planning_panel(self, maneuver_data: Dict) -> None:
        """Create maneuver planning and execution panel"""
        
        st.subheader("🛰️ Collision Avoidance Maneuvers")
        
        if not maneuver_data:
            st.info("No maneuvers currently planned")
            return
        
        # Maneuver summary
        col1, col2, col3 = st.columns(3)
        
        with col1:
            total_maneuvers = maneuver_data.get('total_maneuvers', 0)
            st.metric("Planned Maneuvers", total_maneuvers)
        
        with col2:
            total_dv = maneuver_data.get('total_delta_v_cost', 0)
            st.metric("Total ΔV Required", f"{total_dv:.2f} m/s")
        
        with col3:
            avg_success = maneuver_data.get('average_success_probability', 0)
            st.metric("Avg Success Rate", f"{avg_success:.1%}")
        
        # Complexity distribution
        if 'complexity_distribution' in maneuver_data:
            complexity_dist = maneuver_data['complexity_distribution']
            
            fig_complexity = px.pie(
                values=list(complexity_dist.values()),
                names=list(complexity_dist.keys()),
                title="Maneuver Complexity Distribution"
            )
            fig_complexity.update_layout(height=300)
            st.plotly_chart(fig_complexity, use_container_width=True)
    
    def create_satellite_info_panel(self, satellite_data: Dict) -> None:
        """Create satellite information and status panel"""
        
        st.subheader("📡 Satellite Status")
        
        if not satellite_data:
            st.info("No satellite data available")
            return
        
        # Create satellite status table
        sat_info = []
        for sat_id, position in satellite_data.items():
            altitude = np.linalg.norm(position) - 6371.0  # Earth radius
            sat_info.append({
                'Satellite ID': sat_id,
                'Altitude (km)': f"{altitude:.1f}",
                'Position X (km)': f"{position[0]:.1f}",
                'Position Y (km)': f"{position[1]:.1f}",
                'Position Z (km)': f"{position[2]:.1f}"
            })
        
        if sat_info:
            df = pd.DataFrame(sat_info)
            st.dataframe(df, use_container_width=True)
    
    def create_time_simulation_controls(self) -> Dict:
        """Create time simulation control widgets"""
        
        st.subheader("⏱️ Time Simulation Controls")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            simulation_speed = st.selectbox(
                "Simulation Speed",
                options=[0.1, 0.5, 1.0, 5.0, 10.0, 60.0],
                index=2,  # Default to 1.0x
                format_func=lambda x: f"{x}x real-time" if x >= 1 else f"1/{int(1/x)}x real-time"
            )
        
        with col2:
            prediction_hours = st.slider(
                "Prediction Window (hours)",
                min_value=1,
                max_value=168,  # 7 days
                value=24,
                step=1
            )
        
        with col3:
            auto_update = st.checkbox("Auto-update", value=True)
        
        # Time step controls
        col4, col5 = st.columns(2)
        
        with col4:
            if st.button("⏮️ Step Backward"):
                pass  # Handled by main app
        
        with col5:
            if st.button("⏭️ Step Forward"):
                pass  # Handled by main app
        
        # Current simulation time
        current_time = datetime.utcnow()
        st.write(f"**Current Time:** {current_time.strftime('%Y-%m-%d %H:%M:%S UTC')}")
        
        return {
            'simulation_speed': simulation_speed,
            'prediction_hours': prediction_hours,
            'auto_update': auto_update
        }
    
    def create_system_status_panel(self, system_status: Dict) -> None:
        """Create system status and performance panel"""
        
        st.subheader("⚡ System Status")
        
        # System metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            data_age = system_status.get('data_age_minutes', 0)
            st.metric("Data Age", f"{data_age:.1f} min")
        
        with col2:
            update_rate = system_status.get('update_rate_hz', 0)
            st.metric("Update Rate", f"{update_rate:.2f} Hz")
        
        with col3:
            objects_tracked = system_status.get('objects_tracked', 0)
            st.metric("Objects Tracked", objects_tracked)
        
        with col4:
            system_health = system_status.get('system_health', 'Unknown')
            health_color = {
                'Healthy': 'green',
                'Warning': 'orange', 
                'Error': 'red',
                'Unknown': 'gray'
            }.get(system_health, 'gray')
            
            st.markdown(f"**System Health:** <span style='color:{health_color}'>{system_health}</span>", 
                       unsafe_allow_html=True)

class AdvancedVisualizations:
    """Advanced visualization components"""
    
    def create_orbital_elements_chart(self, satellite_data: Dict) -> go.Figure:
        """Create orbital elements comparison chart"""
        
        if not satellite_data:
            return go.Figure()
        
        # Create subplot for multiple orbital parameters
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Altitude Distribution", "Orbital Velocity", 
                          "Inclination Angles", "Eccentricity"),
            specs=[[{"type": "histogram"}, {"type": "scatter"}],
                   [{"type": "histogram"}, {"type": "histogram"}]]
        )
        
        # Calculate orbital parameters
        altitudes = []
        velocities = []
        
        for position in satellite_data.values():
            altitude = np.linalg.norm(position) - 6371.0
            # Approximate circular orbital velocity
            velocity = np.sqrt(398600.4418 / np.linalg.norm(position))
            
            altitudes.append(altitude)
            velocities.append(velocity)
        
        # Add histograms
        fig.add_trace(go.Histogram(x=altitudes, name="Altitude"), row=1, col=1)
        fig.add_trace(go.Scatter(x=altitudes, y=velocities, mode='markers', name="Vel vs Alt"), row=1, col=2)
        
        # Generate synthetic inclination and eccentricity data for demo
        inclinations = np.random.uniform(0, 180, len(altitudes))
        eccentricities = np.random.beta(2, 5, len(altitudes))  # Mostly circular
        
        fig.add_trace(go.Histogram(x=inclinations, name="Inclination"), row=2, col=1)
        fig.add_trace(go.Histogram(x=eccentricities, name="Eccentricity"), row=2, col=2)
        
        fig.update_layout(height=600, showlegend=False, title="Orbital Elements Analysis")
        
        return fig
    
    def create_collision_timeline_chart(self, predictions: List[Dict]) -> go.Figure:
        """Create timeline chart of collision predictions"""
        
        if not predictions:
            return go.Figure()
        
        # Prepare timeline data
        times = [pred['timestamp'] for pred in predictions]
        probabilities = [pred['collision_probability'] for pred in predictions]
        satellite_ids = [pred.get('satellite_id', 'Unknown') for pred in predictions]
        
        # Create timeline scatter plot
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=times,
            y=probabilities,
            mode='markers+lines',
            marker=dict(
                size=10,
                color=probabilities,
                colorscale='Reds',
                showscale=True,
                colorbar=dict(title="Collision Probability")
            ),
            text=satellite_ids,
            name="Collision Events",
            hovertemplate=(
                "<b>Collision Prediction</b><br>"
                "Time: %{x}<br>"
                "Probability: %{y:.2%}<br>"
                "Satellite: %{text}<br>"
                "<extra></extra>"
            )
        ))
        
        fig.update_layout(
            title="Collision Timeline",
            xaxis_title="Time",
            yaxis_title="Collision Probability",
            height=400,
            yaxis=dict(tickformat='.1%')
        )
        
        return fig

# Main UI orchestration functions
def create_sidebar_controls() -> Dict:
    """Create sidebar control panel"""
    
    st.sidebar.title("🛰️ Control Panel")
    
    # Data source selection
    st.sidebar.subheader("Data Sources")
    use_live_data = st.sidebar.checkbox("Use Live TLE Data", value=True)
    use_synthetic_debris = st.sidebar.checkbox("Include Synthetic Debris", value=True)
    
    # Display options
    st.sidebar.subheader("Display Options")
    max_satellites = st.sidebar.slider("Max Satellites", 5, 100, 20)
    max_debris = st.sidebar.slider("Max Debris Objects", 50, 1000, 200)
    show_trajectories = st.sidebar.checkbox("Show Trajectories", value=True)
    show_risk_zones = st.sidebar.checkbox("Show Risk Zones", value=False)
    
    # Analysis parameters
    st.sidebar.subheader("Analysis Parameters")
    risk_threshold = st.sidebar.slider("Risk Threshold", 0.0, 1.0, 0.1, 0.01)
    prediction_accuracy = st.sidebar.selectbox(
        "Prediction Accuracy", 
        ["High (Slow)", "Medium", "Fast (Lower accuracy)"],
        index=1
    )
    
    # Export options
    st.sidebar.subheader("Export & Actions")
    if st.sidebar.button("📊 Export Data"):
        st.sidebar.success("Data exported successfully!")
    
    if st.sidebar.button("🔄 Refresh All Data"):
        st.sidebar.info("Refreshing data sources...")
    
    return {
        'use_live_data': use_live_data,
        'use_synthetic_debris': use_synthetic_debris,
        'max_satellites': max_satellites,
        'max_debris': max_debris,
        'show_trajectories': show_trajectories,
        'show_risk_zones': show_risk_zones,
        'risk_threshold': risk_threshold,
        'prediction_accuracy': prediction_accuracy
    }

def display_header():
    """Display application header and title"""
    
    # Custom CSS for styling
    st.markdown("""
    <style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .metric-container {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #1e3c72;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div class="main-header">
        <h1>🛰️ Live Orbital Ballet</h1>
        <h3>AI-Powered Satellite Tracking & Collision Avoidance System</h3>
        <p>Real-time orbital mechanics • AI collision detection • Automated maneuver planning</p>
    </div>
    """, unsafe_allow_html=True)

# Example usage and testing
if __name__ == "__main__":
    st.set_page_config(
        page_title="Live Orbital Ballet", 
        page_icon="🛰️",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Display header
    display_header()
    
    # Create sidebar controls
    controls = create_sidebar_controls()
    
    # Initialize dashboard components
    dashboard = DashboardComponents()
    
    # Test with dummy data
    test_satellite_data = {
        25544: [6700, 0, 0],     # ISS-like orbit
        12345: [7200, 1000, 500], # Another satellite
        67890: [6900, -800, 300]  # Third satellite
    }
    
    test_risk_data = {
        'statistics': {
            'total_events': 15,
            'high_risk_events': 3,
            'max_collision_probability': 0.08,
            'events_next_24h': 7,
            'risk_distribution': {'low': 8, 'medium': 4, 'high': 2, 'critical': 1}
        }
    }
    
    test_maneuver_data = {
        'total_maneuvers': 3,
        'total_delta_v_cost': 12.5,
        'average_success_probability': 0.87,
        'complexity_distribution': {'simple': 2, 'moderate': 1, 'complex': 0}
    }
    
    test_system_status = {
        'data_age_minutes': 2.3,
        'update_rate_hz': 0.5,
        'objects_tracked': 157,
        'system_health': 'Healthy'
    }
    
    # Create main layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Main 3D visualization
        fig_3d = dashboard.create_main_3d_plot(test_satellite_data, [])
        st.plotly_chart(fig_3d, use_container_width=True)
        
        # Time simulation controls
        time_controls = dashboard.create_time_simulation_controls()
    
    with col2:
        # Risk assessment panel
        dashboard.create_risk_assessment_panel(test_risk_data)
        
        # Maneuver planning panel  
        dashboard.create_maneuver_planning_panel(test_maneuver_data)
        
        # System status
        dashboard.create_system_status_panel(test_system_status)
    
    # Additional panels in full width
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        dashboard.create_satellite_info_panel(test_satellite_data)
    
    with col4:
        # Advanced visualizations
        advanced_viz = AdvancedVisualizations()
        orbital_chart = advanced_viz.create_orbital_elements_chart(test_satellite_data)
        st.plotly_chart(orbital_chart, use_container_width=True)