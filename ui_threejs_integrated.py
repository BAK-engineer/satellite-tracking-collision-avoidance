"""
Live Orbital Ballet - Three.js Integration
Complete satellite tracking system with enhanced Three.js 3D visualization
"""

import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import time
import os
import json
import asyncio
import websockets
from pathlib import Path

# Import our modules
from data_enhanced import SatelliteDataManager
from database.models import Satellite, ManeuverPlan, RiskAssessment
from database.connection import DatabaseManager
from html_integrator import HTMLIntegrator

# Page configuration
st.set_page_config(
    page_title="Live Orbital Ballet - Three.js Simulation",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Database setup
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/orbital_ballet')
db_manager = DatabaseManager(DATABASE_URL)
html_integrator = HTMLIntegrator()

@st.cache_resource
def get_data_manager():
    """Initialize the satellite data manager"""
    return SatelliteDataManager(DATABASE_URL)

def convert_satellite_data_for_threejs(satellites_df):
    """Convert satellite DataFrame to Three.js compatible format"""
    threejs_data = {
        "satellites": [],
        "debris": [],
        "timestamp": datetime.now().isoformat()
    }
    
    for _, sat in satellites_df.iterrows():
        sat_data = {
            "id": f"sat_{sat['satellite_id']}",
            "name": sat['name'][:20],  # Truncate long names
            "norad_id": sat.get('satellite_id', 0),
            "position": {
                "x": float(sat['x']),
                "y": float(sat['y']), 
                "z": float(sat['z'])
            },
            "velocity": {
                "x": float(sat.get('vx', 0)),
                "y": float(sat.get('vy', 0)),
                "z": float(sat.get('vz', 0))
            },
            "altitude": float(sat['altitude']),
            "velocity_magnitude": float(sat['velocity']),
            "color": "0xff0000" if sat.get('is_maneuvering', False) else "0x00ff9f",
            "size": 3 if sat['name'].upper().startswith('ISS') else 2,
            "is_maneuvering": sat.get('is_maneuvering', False),
            "mission_type": classify_satellite_mission(sat['name'])
        }
        threejs_data["satellites"].append(sat_data)
    
    # Add some simulated debris
    for i in range(20):
        debris_data = {
            "id": f"debris_{i}",
            "name": f"DEBRIS-{1000 + i}",
            "position": {
                "x": np.random.uniform(-20000, 20000),
                "y": np.random.uniform(-20000, 20000),
                "z": np.random.uniform(-20000, 20000)
            },
            "color": "0x808080",
            "size": 1,
            "type": "debris"
        }
        threejs_data["debris"].append(debris_data)
    
    return threejs_data

def classify_satellite_mission(name):
    """Classify satellite based on name"""
    name_upper = name.upper()
    if 'ISS' in name_upper or 'ZARYA' in name_upper:
        return 'space_station'
    elif 'STARLINK' in name_upper:
        return 'communication'
    elif 'GPS' in name_upper or 'NAVSTAR' in name_upper:
        return 'navigation'
    elif 'HUBBLE' in name_upper or 'TELESCOPE' in name_upper:
        return 'science'
    elif 'WEATHER' in name_upper or 'NOAA' in name_upper:
        return 'weather'
    else:
        return 'other'

def create_enhanced_threejs_html(satellite_data):
    """Create enhanced Three.js HTML with real satellite data"""
    # Load the base Three.js template
    template_path = Path("templates/threejs_orbital_simulation.html")
    if not template_path.exists():
        st.error("Three.js template not found!")
        return ""
    
    with open(template_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Inject real satellite data
    data_injection_script = f"""
    <script>
        // Real satellite data from Streamlit
        window.realSatelliteData = {json.dumps(satellite_data)};
        
        // Enhanced satellite creation with real data
        function createRealSatellites() {{
            const realData = window.realSatelliteData.satellites;
            realData.forEach(sat => {{
                const geometry = new THREE.BoxGeometry(sat.size, sat.size, sat.size * 2);
                const material = new THREE.MeshPhongMaterial({{ 
                    color: parseInt(sat.color),
                    emissive: parseInt(sat.color),
                    emissiveIntensity: sat.is_maneuvering ? 0.4 : 0.2
                }});
                
                const mesh = new THREE.Mesh(geometry, material);
                mesh.position.set(
                    sat.position.x / 200,
                    sat.position.y / 200,
                    sat.position.z / 200
                );
                
                mesh.userData = sat;
                satellites[sat.id] = mesh;
                satelliteGroup.add(mesh);
                
                // Add enhanced label with mission info
                const label = createEnhancedLabel(sat.name, sat.mission_type, parseInt(sat.color));
                label.position.set(0, sat.size + 3, 0);
                mesh.add(label);
                
                // Add thrust vector if maneuvering
                if (sat.is_maneuvering) {{
                    const thrustGeometry = new THREE.ConeGeometry(1, 8, 8);
                    const thrustMaterial = new THREE.MeshPhongMaterial({{ 
                        color: 0xffff00,
                        emissive: 0xffff00,
                        emissiveIntensity: 0.5
                    }});
                    const thrustVector = new THREE.Mesh(thrustGeometry, thrustMaterial);
                    thrustVector.position.set(0, -sat.size - 5, 0);
                    thrustVector.rotation.x = Math.PI;
                    mesh.add(thrustVector);
                }}
            }});
            
            // Update counters
            updateCounters();
            updateSatelliteList();
        }}
        
        function createEnhancedLabel(name, missionType, color) {{
            const canvas = document.createElement('canvas');
            const context = canvas.getContext('2d');
            canvas.width = 300;
            canvas.height = 80;
            
            // Background
            context.fillStyle = 'rgba(0, 0, 0, 0.7)';
            context.fillRect(0, 0, 300, 80);
            
            // Border
            context.strokeStyle = `#${color.toString(16).padStart(6, '0')}`;
            context.lineWidth = 2;
            context.strokeRect(2, 2, 296, 76);
            
            // Text
            context.fillStyle = `#${color.toString(16).padStart(6, '0')}`;
            context.font = '18px Courier New';
            context.textAlign = 'center';
            context.fillText(name, 150, 30);
            
            context.font = '12px Courier New';
            context.fillStyle = '#ffffff';
            context.fillText(`Type: ${missionType.toUpperCase()}`, 150, 55);
            
            const texture = new THREE.CanvasTexture(canvas);
            const material = new THREE.SpriteMaterial({{ map: texture, transparent: true }});
            const sprite = new THREE.Sprite(material);
            sprite.scale.set(30, 8, 1);
            return sprite;
        }}
        
        // Override the original createSatellites function
        const originalInit = init;
        init = async function() {{
            await originalInit();
            // Clear default satellites and use real data
            satelliteGroup.clear();
            createRealSatellites();
        }};
        
        // Streamlit communication bridge
        window.streamlitBridge.onStreamlitData(function(data) {{
            if (data.type === 'satellite_update') {{
                updateRealTimeData(data.satellites);
            }} else if (data.type === 'maneuver_start') {{
                startManeuverVisualization(data.satellite_id);
            }} else if (data.type === 'camera_focus') {{
                focusOnSatellite(data.satellite_id);
            }}
        }});
        
        function updateRealTimeData(satelliteUpdates) {{
            satelliteUpdates.forEach(sat => {{
                if (satellites[sat.id]) {{
                    // Smooth position transition
                    const targetPos = new THREE.Vector3(
                        sat.position.x / 200,
                        sat.position.y / 200,
                        sat.position.z / 200
                    );
                    
                    satellites[sat.id].position.lerp(targetPos, 0.1);
                    
                    // Update maneuvering status
                    if (sat.is_maneuvering !== satellites[sat.id].userData.is_maneuvering) {{
                        satellites[sat.id].userData.is_maneuvering = sat.is_maneuvering;
                        updateSatelliteVisuals(satellites[sat.id]);
                    }}
                }}
            }});
        }}
        
        function startManeuverVisualization(satelliteId) {{
            const sat = satellites[satelliteId];
            if (sat) {{
                // Add particle system for maneuver effect
                const particles = new THREE.Group();
                for (let i = 0; i < 20; i++) {{
                    const particleGeometry = new THREE.SphereGeometry(0.2, 4, 4);
                    const particleMaterial = new THREE.MeshBasicMaterial({{ 
                        color: 0xffff00,
                        transparent: true,
                        opacity: 0.8
                    }});
                    const particle = new THREE.Mesh(particleGeometry, particleMaterial);
                    particle.position.set(
                        (Math.random() - 0.5) * 10,
                        (Math.random() - 0.5) * 10,
                        (Math.random() - 0.5) * 10
                    );
                    particles.add(particle);
                }}
                sat.add(particles);
                
                // Remove particles after 5 seconds
                setTimeout(() => {{
                    sat.remove(particles);
                }}, 5000);
            }}
        }}
        
        function focusOnSatellite(satelliteId) {{
            const sat = satellites[satelliteId];
            if (sat) {{
                controls.target.copy(sat.position);
                camera.position.copy(sat.position);
                camera.position.add(new THREE.Vector3(50, 30, 50));
                controls.update();
            }}
        }}
    </script>
    """
    
    # Insert the script before closing body tag
    html_content = html_content.replace('</body>', f'{data_injection_script}</body>')
    
    return html_content

def main():
    st.title("🚀 Live Orbital Ballet - Three.js 3D Simulation")
    st.markdown("**Enhanced 3D satellite tracking with real-time orbital simulation**")
    
    # Initialize data manager
    data_manager = get_data_manager()
    
    # Create main layout
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.header("🎮 Mission Control")
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=True)
        refresh_interval = st.slider("Refresh Rate (seconds)", 5, 60, 10)
        
        # Simulation controls
        st.subheader("🎯 Simulation Controls")
        
        col2a, col2b = st.columns(2)
        with col2a:
            if st.button("🌍 Reset View"):
                st.session_state['camera_action'] = 'reset'
            if st.button("🛰️ Follow ISS"):
                st.session_state['camera_action'] = 'follow_iss'
        
        with col2b:
            if st.button("⏸️ Pause"):
                st.session_state['sim_action'] = 'pause'
            if st.button("▶️ Play"):
                st.session_state['sim_action'] = 'play'
        
        # Time controls
        st.subheader("⏱️ Time Control")
        time_speed = st.selectbox("Time Speed", [0.1, 0.5, 1, 5, 10, 50, 100], index=2)
        
        # Display options
        st.subheader("👁️ Display Options")
        show_satellites = st.checkbox("Show Satellites", value=True)
        show_debris = st.checkbox("Show Debris", value=True)
        show_orbits = st.checkbox("Show Orbital Paths", value=False)
        show_labels = st.checkbox("Show Labels", value=True)
        
        # Satellite selection
        st.subheader("📡 Satellite Focus")
        try:
            satellites_df = data_manager.get_current_positions()
            if not satellites_df.empty:
                satellite_names = ['None'] + satellites_df['name'].tolist()
                selected_satellite = st.selectbox("Focus on Satellite", satellite_names)
                
                if selected_satellite != 'None':
                    if st.button("🎯 Focus Camera"):
                        sat_row = satellites_df[satellites_df['name'] == selected_satellite].iloc[0]
                        st.session_state['focus_satellite'] = f"sat_{sat_row['satellite_id']}"
        except Exception as e:
            st.error(f"Error loading satellites: {str(e)}")
            satellites_df = pd.DataFrame()
    
    with col1:
        try:
            # Get current satellite data
            if satellites_df.empty:
                satellites_df = get_data_manager().get_current_positions()
            
            if satellites_df.empty:
                st.warning("No satellite data available. Using demo mode.")
                # Create demo data
                satellites_df = pd.DataFrame({
                    'satellite_id': [25544, 20580, 44713],
                    'name': ['ISS (ZARYA)', 'HUBBLE SPACE TELESCOPE', 'STARLINK-1007'],
                    'x': [6500000, 5800000, 7200000],
                    'y': [1200000, -2100000, 800000],
                    'z': [2100000, 3400000, -1500000],
                    'altitude': [408.2, 547.0, 550.0],
                    'velocity': [7.66, 7.59, 7.56]
                })
            
            # Convert data for Three.js
            threejs_data = convert_satellite_data_for_threejs(satellites_df)
            
            # Create enhanced Three.js HTML
            enhanced_html = create_enhanced_threejs_html(threejs_data)
            
            # Display system status
            st.subheader("📊 System Status")
            status_col1, status_col2, status_col3, status_col4 = st.columns(4)
            
            with status_col1:
                st.metric("🛰️ Satellites", len(threejs_data['satellites']))
            with status_col2:
                st.metric("🗂️ Debris Objects", len(threejs_data['debris']))
            with status_col3:
                active_maneuvers = len([s for s in threejs_data['satellites'] if s['is_maneuvering']])
                st.metric("🚀 Active Maneuvers", active_maneuvers)
            with status_col4:
                st.metric("⚡ Time Speed", f"{time_speed}x")
            
            # Render the Three.js simulation
            st.subheader("🌍 3D Orbital Simulation")
            
            # Prepare data for injection
            real_time_data = {
                'satellites': threejs_data['satellites'],
                'debris': threejs_data['debris'],
                'controls': {
                    'time_speed': time_speed,
                    'show_satellites': show_satellites,
                    'show_debris': show_debris,
                    'show_orbits': show_orbits,
                    'show_labels': show_labels
                },
                'actions': {
                    'camera_action': st.session_state.get('camera_action', ''),
                    'focus_satellite': st.session_state.get('focus_satellite', ''),
                    'sim_action': st.session_state.get('sim_action', '')
                }
            }
            
            # Render the Three.js component
            component_return = html_integrator.render_html(
                enhanced_html, 
                height=700, 
                key="threejs_simulation",
                data=real_time_data
            )
            
            # Handle component return data
            if component_return:
                try:
                    returned_data = json.loads(component_return) if isinstance(component_return, str) else component_return
                    if returned_data.get('event') == 'satellite_selected':
                        st.info(f"Selected satellite: {returned_data.get('satellite_name', 'Unknown')}")
                except:
                    pass
            
            # Clear session state actions
            if 'camera_action' in st.session_state:
                del st.session_state['camera_action']
            if 'focus_satellite' in st.session_state:
                del st.session_state['focus_satellite']
            if 'sim_action' in st.session_state:
                del st.session_state['sim_action']
            
        except Exception as e:
            st.error(f"Error in 3D simulation: {str(e)}")
            st.info("Using fallback 2D visualization...")
            
            # Fallback to 2D Plotly visualization
            if not satellites_df.empty:
                fig = go.Figure()
                
                # Add Earth
                theta = np.linspace(0, 2*np.pi, 50)
                phi = np.linspace(0, np.pi, 50)
                theta, phi = np.meshgrid(theta, phi)
                
                earth_radius = 6371
                x_earth = earth_radius * np.sin(phi) * np.cos(theta)
                y_earth = earth_radius * np.sin(phi) * np.sin(theta)
                z_earth = earth_radius * np.cos(phi)
                
                fig.add_trace(go.Surface(
                    x=x_earth, y=y_earth, z=z_earth,
                    colorscale='earth',
                    opacity=0.8,
                    showscale=False,
                    name='Earth'
                ))
                
                # Add satellites
                fig.add_trace(go.Scatter3d(
                    x=satellites_df['x']/1000,
                    y=satellites_df['y']/1000,
                    z=satellites_df['z']/1000,
                    mode='markers',
                    marker=dict(size=8, color='cyan'),
                    text=satellites_df['name'],
                    name='Satellites'
                ))
                
                fig.update_layout(
                    title="3D Satellite Tracking (Fallback Mode)",
                    scene=dict(
                        xaxis_title="X (km)",
                        yaxis_title="Y (km)", 
                        zaxis_title="Z (km)",
                        aspectmode='cube'
                    ),
                    height=700
                )
                
                st.plotly_chart(fig, use_container_width=True)
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(refresh_interval)
        st.rerun()

if __name__ == "__main__":
    main()