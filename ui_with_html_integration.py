"""
Live Orbital Ballet - Enhanced UI with Full HTML Integration
Complete satellite tracking system with custom HTML integration capabilities
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
import json
from pathlib import Path

# Import our modules
from data_enhanced import SatelliteDataManager
from database.models import Satellite, ManeuverPlan, RiskAssessment
from database.connection import DatabaseManager
from html_integrator import HTMLIntegrator, integrate_html_into_app

# Page configuration
st.set_page_config(
    page_title="Live Orbital Ballet - HTML Integration",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/orbital_ballet')
db_manager = DatabaseManager(DATABASE_URL)

# Initialize HTML integrator
html_integrator = HTMLIntegrator()

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
    
    # Update layout
    fig.update_layout(
        title="Live Orbital Ballet - 3D Satellite Tracking",
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
        height=500,
        paper_bgcolor='black',
        font=dict(color='white')
    )
    
    return fig

def main():
    st.title("🛰️ Live Orbital Ballet - HTML Integration System")
    st.markdown("Complete satellite tracking with custom HTML integration capabilities")
    
    # Create main tabs
    main_tab, html_tab, templates_tab, integration_tab = st.tabs([
        "🛰️ Satellite Tracking", 
        "🌐 HTML Integration", 
        "📋 Templates", 
        "🔧 Live Integration"
    ])
    
    with main_tab:
        # Initialize data manager
        data_manager = get_data_manager()
        
        # Sidebar controls
        st.sidebar.header("🎮 Mission Control")
        
        # Auto-refresh toggle
        auto_refresh = st.sidebar.checkbox("Auto-refresh (10s)", value=True)
        
        # Manual refresh button
        if st.sidebar.button("🔄 Refresh Data"):
            st.cache_resource.clear()
            st.rerun()
        
        try:
            # Get current satellite data
            satellites_df = data_manager.get_current_positions()
            
            if satellites_df.empty:
                st.error("No satellite data available. Please check your data source.")
                return
            
            # Get active maneuvers (simulated)
            active_maneuvers = []
            if 'maneuver_plans' in st.session_state:
                active_maneuvers = [m for m in st.session_state.maneuver_plans if m['status'] == 'active']
            
            # Main content area
            col1, col2 = st.columns([2, 1])
            
            with col1:
                # 3D Visualization
                fig_3d = create_maneuver_visualization(satellites_df, active_maneuvers)
                st.plotly_chart(fig_3d, use_container_width=True)
            
            with col2:
                # System status
                st.subheader("📊 System Status")
                
                total_satellites = len(satellites_df)
                active_maneuver_count = len(active_maneuvers)
                
                st.metric("Total Satellites", total_satellites)
                st.metric("Active Maneuvers", active_maneuver_count)
                
                # Real-time data for HTML integration
                system_data = {
                    "satellites": total_satellites,
                    "active_maneuvers": active_maneuver_count,
                    "system_health": "OPTIMAL",
                    "data_age": "15s",
                    "timestamp": datetime.now().isoformat()
                }
                
                # Store data in session state for HTML integration
                st.session_state['system_data'] = system_data
            
            # Real-time updates
            if auto_refresh:
                time.sleep(10)
                st.rerun()
                
        except Exception as e:
            st.error(f"Error loading satellite data: {str(e)}")
            st.info("Make sure the database is running and accessible.")
    
    with html_tab:
        st.header("🌐 HTML File Integration")
        st.markdown("Upload any HTML file to integrate into your satellite tracking system!")
        
        # Create sub-tabs for different integration methods
        upload_tab, editor_tab, preview_tab = st.tabs(["📁 Upload", "✏️ Editor", "👁️ Preview"])
        
        with upload_tab:
            st.subheader("Upload Your HTML File")
            
            # File uploader
            uploaded_file = st.file_uploader(
                "Choose HTML file",
                type=['html', 'htm'],
                help="Upload any HTML file. CSS, JS, and images will be automatically processed."
            )
            
            if uploaded_file is not None:
                # Read and process the file
                html_content = uploaded_file.read().decode('utf-8')
                
                # Save to templates
                template_name = uploaded_file.name.replace('.html', '').replace('.htm', '')
                template_path = html_integrator.templates_dir / uploaded_file.name
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                
                st.success(f"✅ HTML file '{uploaded_file.name}' uploaded successfully!")
                
                # Configuration options
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("⚙️ Configuration")
                    height = st.slider("Component Height", 200, 1000, 600, key="upload_height")
                    
                    # Data injection options
                    inject_data = st.checkbox("Inject Real-time Satellite Data", key="upload_data")
                    
                    if inject_data and 'system_data' in st.session_state:
                        st.json(st.session_state['system_data'])
                
                with col2:
                    st.subheader("🖼️ Rendered HTML")
                    # Render the uploaded HTML
                    data_to_inject = st.session_state.get('system_data', {}) if inject_data else None
                    html_integrator.render_html(
                        html_content,
                        height=height,
                        key="uploaded_html_render",
                        data=data_to_inject
                    )
        
        with editor_tab:
            st.subheader("✏️ HTML Code Editor")
            
            # Sample templates for quick start
            sample_templates = {
                "Custom Dashboard": """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #1e3c72, #2a5298); color: white; margin: 0; padding: 20px; }
        .dashboard { background: rgba(255,255,255,0.1); padding: 20px; border-radius: 15px; backdrop-filter: blur(10px); }
        .metric { display: inline-block; margin: 10px; padding: 15px; background: rgba(0,255,159,0.2); border-radius: 8px; border: 1px solid #00ff9f; }
        .metric-value { font-size: 24px; font-weight: bold; color: #00ff9f; }
        .metric-label { font-size: 12px; opacity: 0.8; }
        button { background: #00ff9f; color: black; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-weight: bold; }
        button:hover { background: #00d4aa; }
    </style>
</head>
<body>
    <div class="dashboard">
        <h2>🛰️ Custom Satellite Dashboard</h2>
        <div class="metric">
            <div class="metric-value" data-streamlit-bind="satellites">0</div>
            <div class="metric-label">Total Satellites</div>
        </div>
        <div class="metric">
            <div class="metric-value" data-streamlit-bind="active_maneuvers">0</div>
            <div class="metric-label">Active Maneuvers</div>
        </div>
        <div class="metric">
            <div class="metric-value" data-streamlit-bind="system_health">OK</div>
            <div class="metric-label">System Health</div>
        </div>
        <br><br>
        <button data-streamlit-event="click" data-streamlit-data='{"action": "refresh_satellites"}'>🔄 Refresh Data</button>
        <button data-streamlit-event="click" data-streamlit-data='{"action": "emergency_stop"}'>🚨 Emergency Stop</button>
    </div>
</body>
</html>""",
                "Orbital Map": """<!DOCTYPE html>
<html>
<head>
    <style>
        body { margin: 0; font-family: Arial, sans-serif; background: #000; color: #00ff9f; }
        .map-container { position: relative; height: 400px; background: radial-gradient(circle, #001122 0%, #000000 100%); border: 2px solid #00ff9f; border-radius: 10px; overflow: hidden; }
        .satellite { position: absolute; width: 8px; height: 8px; background: #00ff9f; border-radius: 50%; box-shadow: 0 0 10px #00ff9f; animation: pulse 2s infinite; }
        .satellite.maneuvering { background: #ff6b6b; box-shadow: 0 0 10px #ff6b6b; }
        .controls { position: absolute; top: 10px; right: 10px; background: rgba(0,0,0,0.8); padding: 10px; border-radius: 5px; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }
        .info-panel { position: absolute; bottom: 10px; left: 10px; background: rgba(0,0,0,0.8); padding: 10px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="map-container">
        <div class="controls">
            <div>Tracked: <span data-streamlit-bind="satellites">0</span></div>
            <div>Active: <span data-streamlit-bind="active_maneuvers">0</span></div>
            <button data-streamlit-event="click" data-streamlit-data='{"action": "center_view"}' style="background: #00ff9f; color: black; border: none; padding: 5px 10px; border-radius: 3px; margin-top: 5px; cursor: pointer;">Center View</button>
        </div>
        <div class="satellite" style="top: 20%; left: 30%;"></div>
        <div class="satellite maneuvering" style="top: 60%; left: 70%;"></div>
        <div class="satellite" style="top: 80%; left: 20%;"></div>
        <div class="satellite" style="top: 40%; left: 80%;"></div>
        <div class="info-panel">
            <div>🛰️ Live Orbital Map</div>
            <div>Status: <span data-streamlit-bind="system_health">OK</span></div>
        </div>
    </div>
</body>
</html>"""
            }
            
            # Template selector
            selected_template = st.selectbox(
                "Choose Template",
                ["Custom"] + list(sample_templates.keys()),
                key="editor_template"
            )
            
            # Initialize HTML content
            if selected_template != "Custom":
                initial_html = sample_templates[selected_template]
            else:
                initial_html = ""
            
            # HTML editor
            html_content = st.text_area(
                "HTML Content",
                value=initial_html,
                height=300,
                help="Edit your HTML content here. Use data-streamlit-bind for data binding and data-streamlit-event for interactions.",
                key="html_editor_content"
            )
            
            if html_content.strip():
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("⚙️ Configuration")
                    height = st.slider("Height", 200, 1000, 400, key="editor_height")
                    
                    # Data injection
                    use_data = st.checkbox("Use Real-time Data", key="editor_data")
                    
                    if use_data and 'system_data' in st.session_state:
                        st.json(st.session_state['system_data'])
                
                with col2:
                    st.subheader("🖼️ Live Preview")
                    data_to_inject = st.session_state.get('system_data', {}) if use_data else None
                    html_integrator.render_html(
                        html_content,
                        height=height,
                        key="editor_html_render",
                        data=data_to_inject
                    )
        
        with preview_tab:
            st.subheader("👁️ HTML Source Preview")
            
            if 'html_editor_content' in st.session_state and st.session_state['html_editor_content']:
                html_to_preview = st.session_state['html_editor_content']
            else:
                html_to_preview = "No HTML content to preview. Use the Editor tab to create content."
            
            st.code(html_to_preview, language='html')
    
    with templates_tab:
        st.header("📋 Available Templates")
        
        # List available templates
        templates = html_integrator.list_available_templates()
        
        if templates:
            selected_template = st.selectbox("Select Template", templates, key="template_selector")
            
            if selected_template:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    st.subheader("📄 Template Preview")
                    preview = html_integrator.get_template_preview(selected_template)
                    st.code(preview, language='html')
                
                with col2:
                    st.subheader("🖼️ Rendered Template")
                    template_path = html_integrator.templates_dir / f"{selected_template}.html"
                    content = html_integrator.load_html_file(str(template_path))
                    
                    # Configuration
                    height = st.slider("Height", 200, 1000, 500, key="template_height")
                    use_data = st.checkbox("Inject Live Data", key="template_data")
                    
                    data_to_inject = st.session_state.get('system_data', {}) if use_data else None
                    html_integrator.render_html(
                        content,
                        height=height,
                        key=f"template_{selected_template}",
                        data=data_to_inject
                    )
        else:
            st.info("📂 No templates found. Upload HTML files in the HTML Integration tab to get started!")
            
            # Show built-in templates
            st.subheader("🏗️ Built-in Templates")
            for template_name in ["satellite_info_panel", "mission_control_dashboard", "orbital_map"]:
                template_path = Path("templates") / f"{template_name}.html"
                if template_path.exists():
                    if st.button(f"Load {template_name.replace('_', ' ').title()}", key=f"load_{template_name}"):
                        content = html_integrator.load_html_file(str(template_path))
                        st.subheader(f"🖼️ {template_name.replace('_', ' ').title()}")
                        html_integrator.render_html(content, height=600, key=f"builtin_{template_name}")
    
    with integration_tab:
        st.header("🔧 Live Integration Demo")
        st.markdown("See how HTML integrates with real-time satellite data!")
        
        # Real-time data display
        if 'system_data' in st.session_state:
            st.subheader("📊 Current System Data")
            st.json(st.session_state['system_data'])
        
        # Integration examples
        st.subheader("🎯 Integration Examples")
        
        # Example 1: Simple status panel
        example1_html = """
        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px; color: white; font-family: Arial, sans-serif;">
            <h3>🛰️ Live Status Panel</h3>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px; margin-top: 15px;">
                <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold;" data-streamlit-bind="satellites">0</div>
                    <div style="font-size: 12px; opacity: 0.8;">Satellites</div>
                </div>
                <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold;" data-streamlit-bind="active_maneuvers">0</div>
                    <div style="font-size: 12px; opacity: 0.8;">Active Maneuvers</div>
                </div>
                <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 8px; text-align: center;">
                    <div style="font-size: 24px; font-weight: bold;" data-streamlit-bind="system_health">OK</div>
                    <div style="font-size: 12px; opacity: 0.8;">System Health</div>
                </div>
            </div>
            <button data-streamlit-event="click" data-streamlit-data='{"action": "update_status"}' 
                    style="background: #fff; color: #667eea; border: none; padding: 10px 20px; border-radius: 5px; margin-top: 15px; cursor: pointer; font-weight: bold;">
                🔄 Update Status
            </button>
        </div>
        """
        
        st.markdown("**Example 1: Real-time Status Panel**")
        data_to_inject = st.session_state.get('system_data', {})
        html_integrator.render_html(example1_html, height=200, key="example1", data=data_to_inject)
        
        # Example 2: Interactive mission control
        example2_html = """
        <div style="background: #000; color: #00ff9f; padding: 20px; border-radius: 10px; font-family: 'Courier New', monospace; border: 2px solid #00ff9f;">
            <h3>🎮 Mission Control Interface</h3>
            <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 15px; margin: 15px 0;">
                <div style="background: rgba(0,255,159,0.1); padding: 15px; border-radius: 5px; border: 1px solid #00ff9f;">
                    <div>SATELLITES TRACKED</div>
                    <div style="font-size: 20px; font-weight: bold;" data-streamlit-bind="satellites">0</div>
                </div>
                <div style="background: rgba(0,255,159,0.1); padding: 15px; border-radius: 5px; border: 1px solid #00ff9f;">
                    <div>SYSTEM STATUS</div>
                    <div style="font-size: 20px; font-weight: bold;" data-streamlit-bind="system_health">OK</div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;">
                <button data-streamlit-event="click" data-streamlit-data='{"action": "emergency_stop"}' 
                        style="background: #ff6b6b; color: white; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold;">
                    🚨 EMERGENCY STOP
                </button>
                <button data-streamlit-event="click" data-streamlit-data='{"action": "refresh_data"}' 
                        style="background: #00ff9f; color: black; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold;">
                    🔄 REFRESH DATA
                </button>
                <button data-streamlit-event="click" data-streamlit-data='{"action": "system_check"}' 
                        style="background: #ffd93d; color: black; border: none; padding: 10px; border-radius: 5px; cursor: pointer; font-weight: bold;">
                    🔧 SYSTEM CHECK
                </button>
            </div>
        </div>
        """
        
        st.markdown("**Example 2: Mission Control Interface**")
        html_integrator.render_html(example2_html, height=250, key="example2", data=data_to_inject)

if __name__ == "__main__":
    main()