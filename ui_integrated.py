"""
Integrated Live Orbital Ballet - Enhanced UI with Visual Maneuvering System
Shows satellite tracking with visual maneuver execution and planning
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import math
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

# Import our modules
from data_enhanced import SatelliteDataManager
from database.models import Satellite, ManeuverPlan, RiskAssessment
from database.connection import DatabaseManager

# Page configuration
st.set_page_config(
    page_title="Live Orbital Ballet - Integrated Maneuvering System",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/orbital_ballet')
db_manager = DatabaseManager(DATABASE_URL)

@st.cache_resource
def get_data_manager():
    """Initialize the satellite data manager"""
    return SatelliteDataManager(DATABASE_URL)

def create_maneuver_visualization(satellites_df, active_maneuvers):
    """Create 3D visualization with satellite tracking and maneuver indicators"""
    
    # Create Earth sphere
    theta = np.linspace(0, 2*np.pi, 50)
    phi = np.linspace(0, np.pi, 50)
    theta, phi = np.meshgrid(theta, phi)
    
    earth_radius = 6371  # km
    x_earth = earth_radius * np.sin(phi) * np.cos(theta)
    y_earth = earth_radius * np.sin(phi) * np.sin(theta)
    z_earth = earth_radius * np.cos(phi)
    
    fig = go.Figure()
    
    # Add Earth
    fig.add_trace(go.Surface(
        x=x_earth, y=y_earth, z=z_earth,
        colorscale='earth',
        opacity=0.8,
        showscale=False,
        name='Earth'
    ))
    
    # Color satellites based on maneuver status
    colors = []
    sizes = []
    hover_texts = []
    
    for _, sat in satellites_df.iterrows():
        sat_id = sat['satellite_id']
        has_active_maneuver = sat_id in [m['satellite_id'] for m in active_maneuvers]
        
        if has_active_maneuver:
            colors.append('red')
            sizes.append(12)
            hover_texts.append(f"{sat['name']}<br>🚀 MANEUVERING<br>Alt: {sat['altitude']:.1f} km<br>Vel: {sat['velocity']:.2f} km/s")
        else:
            colors.append('cyan')
            sizes.append(8)
            hover_texts.append(f"{sat['name']}<br>Alt: {sat['altitude']:.1f} km<br>Vel: {sat['velocity']:.2f} km/s")
    
    # Add satellites
    fig.add_trace(go.Scatter3d(
        x=satellites_df['x'],
        y=satellites_df['y'],
        z=satellites_df['z'],
        mode='markers',
        marker=dict(
            size=sizes,
            color=colors,
            opacity=0.8,
            line=dict(width=1, color='white')
        ),
        text=hover_texts,
        hovertemplate='%{text}<extra></extra>',
        name='Satellites'
    ))
    
    # Add maneuver thrust vectors
    for maneuver in active_maneuvers:
        sat = satellites_df[satellites_df['satellite_id'] == maneuver['satellite_id']].iloc[0]
        
        # Calculate thrust vector (simplified visualization)
        thrust_magnitude = maneuver.get('delta_v', 0.1) * 1000  # Scale for visibility
        thrust_direction = np.array([
            np.cos(maneuver.get('thrust_angle_x', 0)),
            np.sin(maneuver.get('thrust_angle_y', 0)),
            np.cos(maneuver.get('thrust_angle_z', 0))
        ])
        
        # Normalize and scale thrust vector
        thrust_direction = thrust_direction / np.linalg.norm(thrust_direction) * thrust_magnitude
        
        # Add thrust vector arrow
        fig.add_trace(go.Scatter3d(
            x=[sat['x'], sat['x'] + thrust_direction[0]],
            y=[sat['y'], sat['y'] + thrust_direction[1]],
            z=[sat['z'], sat['z'] + thrust_direction[2]],
            mode='lines+markers',
            line=dict(color='yellow', width=6),
            marker=dict(size=[0, 10], color=['yellow', 'orange']),
            name=f'Thrust Vector - {sat["name"]}',
            showlegend=False
        ))
    
    # Update layout
    fig.update_layout(
        title="Live Orbital Ballet - 3D Satellite Tracking with Maneuvers",
        scene=dict(
            xaxis_title="X (km)",
            yaxis_title="Y (km)",
            zaxis_title="Z (km)",
            aspectmode='cube',
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            ),
            bgcolor='black'
        ),
        showlegend=True,
        height=600,
        paper_bgcolor='black',
        font=dict(color='white')
    )
    
    return fig

def create_maneuver_timeline(maneuvers):
    """Create timeline visualization of planned and active maneuvers"""
    if not maneuvers:
        return go.Figure().add_annotation(text="No maneuvers planned", xref="paper", yref="paper", x=0.5, y=0.5)
    
    fig = go.Figure()
    
    for i, maneuver in enumerate(maneuvers):
        start_time = maneuver.get('planned_start', datetime.now())
        duration = maneuver.get('duration_seconds', 300)  # Default 5 minutes
        end_time = start_time + timedelta(seconds=duration)
        
        status = maneuver.get('status', 'planned')
        color = {'planned': 'blue', 'active': 'orange', 'completed': 'green', 'failed': 'red'}.get(status, 'gray')
        
        fig.add_trace(go.Scatter(
            x=[start_time, end_time],
            y=[i, i],
            mode='lines+markers',
            line=dict(color=color, width=8),
            marker=dict(size=10),
            name=f"Satellite {maneuver.get('satellite_id', 'Unknown')} - {status.title()}",
            hovertemplate=f"Satellite ID: {maneuver.get('satellite_id', 'Unknown')}<br>" +
                         f"Delta-V: {maneuver.get('delta_v', 0):.3f} km/s<br>" +
                         f"Status: {status.title()}<br>" +
                         f"Start: {start_time}<br>" +
                         f"Duration: {duration}s<extra></extra>"
        ))
    
    fig.update_layout(
        title="Maneuver Timeline",
        xaxis_title="Time",
        yaxis_title="Maneuver Sequence",
        yaxis=dict(tickmode='linear', tick0=0, dtick=1),
        height=300,
        showlegend=True
    )
    
    return fig

def main():
    st.title("🛰️ Live Orbital Ballet - Integrated Maneuvering System")
    st.markdown("Real-time satellite tracking with visual maneuver execution and planning")
    
    # Initialize data manager
    data_manager = get_data_manager()
    
    # Sidebar controls
    st.sidebar.header("Mission Control")
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto-refresh (10s)", value=True)
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_resource.clear()
        st.rerun()
    
    # Maneuver controls
    st.sidebar.subheader("Maneuver Planning")
    
    try:
        # Get current satellite data
        satellites_df = data_manager.get_current_positions()
        
        if satellites_df.empty:
            st.error("No satellite data available. Please check your data source.")
            return
        
        # Satellite selection for maneuver planning
        selected_satellite = st.sidebar.selectbox(
            "Select Satellite for Maneuver",
            options=satellites_df['name'].tolist(),
            key="satellite_select"
        )
        
        # Maneuver parameters
        delta_v = st.sidebar.number_input("Delta-V (km/s)", min_value=0.001, max_value=1.0, value=0.1, step=0.001)
        maneuver_duration = st.sidebar.number_input("Duration (seconds)", min_value=10, max_value=3600, value=300)
        
        # Plan maneuver button
        if st.sidebar.button("📋 Plan Maneuver"):
            selected_sat_data = satellites_df[satellites_df['name'] == selected_satellite].iloc[0]
            
            # Create maneuver plan (simplified)
            maneuver_plan = {
                'satellite_id': selected_sat_data['satellite_id'],
                'satellite_name': selected_satellite,
                'delta_v': delta_v,
                'duration_seconds': maneuver_duration,
                'planned_start': datetime.now() + timedelta(minutes=5),
                'status': 'planned',
                'thrust_angle_x': np.random.uniform(0, 2*np.pi),
                'thrust_angle_y': np.random.uniform(0, 2*np.pi),
                'thrust_angle_z': np.random.uniform(0, 2*np.pi)
            }
            
            # Store in session state
            if 'maneuver_plans' not in st.session_state:
                st.session_state.maneuver_plans = []
            
            st.session_state.maneuver_plans.append(maneuver_plan)
            st.sidebar.success(f"Maneuver planned for {selected_satellite}")
    
        # Execute maneuver button
        if st.sidebar.button("🚀 Execute Next Maneuver"):
            if 'maneuver_plans' in st.session_state and st.session_state.maneuver_plans:
                # Find next planned maneuver
                for maneuver in st.session_state.maneuver_plans:
                    if maneuver['status'] == 'planned':
                        maneuver['status'] = 'active'
                        maneuver['actual_start'] = datetime.now()
                        st.sidebar.success(f"Executing maneuver for {maneuver['satellite_name']}")
                        break
            else:
                st.sidebar.warning("No maneuvers planned")
        
        # Get active maneuvers
        active_maneuvers = []
        if 'maneuver_plans' in st.session_state:
            active_maneuvers = [m for m in st.session_state.maneuver_plans if m['status'] == 'active']
            
            # Simulate maneuver completion
            for maneuver in st.session_state.maneuver_plans:
                if maneuver['status'] == 'active' and 'actual_start' in maneuver:
                    elapsed = (datetime.now() - maneuver['actual_start']).total_seconds()
                    if elapsed > maneuver['duration_seconds']:
                        maneuver['status'] = 'completed'
        
        # Main content area
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # 3D Visualization with maneuvers
            fig_3d = create_maneuver_visualization(satellites_df, active_maneuvers)
            st.plotly_chart(fig_3d, use_container_width=True)
        
        with col2:
            # System status
            st.subheader("System Status")
            
            total_satellites = len(satellites_df)
            active_maneuver_count = len(active_maneuvers)
            
            st.metric("Total Satellites", total_satellites)
            st.metric("Active Maneuvers", active_maneuver_count)
            
            if active_maneuvers:
                st.subheader("🚀 Active Maneuvers")
                for maneuver in active_maneuvers:
                    with st.expander(f"Satellite {maneuver['satellite_name']}"):
                        st.write(f"**Delta-V:** {maneuver['delta_v']:.3f} km/s")
                        st.write(f"**Duration:** {maneuver['duration_seconds']}s")
                        st.write(f"**Status:** {maneuver['status'].title()}")
                        
                        if 'actual_start' in maneuver:
                            elapsed = (datetime.now() - maneuver['actual_start']).total_seconds()
                            progress = min(elapsed / maneuver['duration_seconds'], 1.0)
                            st.progress(progress)
                            st.write(f"**Progress:** {progress*100:.1f}%")
        
        # Maneuver timeline
        if 'maneuver_plans' in st.session_state and st.session_state.maneuver_plans:
            st.subheader("Maneuver Timeline")
            fig_timeline = create_maneuver_timeline(st.session_state.maneuver_plans)
            st.plotly_chart(fig_timeline, use_container_width=True)
        
        # Maneuver history table
        if 'maneuver_plans' in st.session_state and st.session_state.maneuver_plans:
            st.subheader("Maneuver History")
            
            maneuver_data = []
            for maneuver in st.session_state.maneuver_plans:
                maneuver_data.append({
                    'Satellite': maneuver['satellite_name'],
                    'Delta-V (km/s)': maneuver['delta_v'],
                    'Duration (s)': maneuver['duration_seconds'],
                    'Status': maneuver['status'].title(),
                    'Planned Start': maneuver['planned_start'].strftime('%H:%M:%S'),
                    'Actual Start': maneuver.get('actual_start', 'N/A')
                })
            
            df_maneuvers = pd.DataFrame(maneuver_data)
            st.dataframe(df_maneuvers, use_container_width=True)
        
        # Real-time updates
        if auto_refresh:
            time.sleep(10)
            st.rerun()
            
    except Exception as e:
        st.error(f"Error loading satellite data: {str(e)}")
        st.info("Make sure the database is running and accessible.")
        
        # Show connection details for debugging
        with st.expander("Debug Information"):
            st.code(f"Database URL: {DATABASE_URL}")
            st.code(f"Error: {str(e)}")

if __name__ == "__main__":
    main()