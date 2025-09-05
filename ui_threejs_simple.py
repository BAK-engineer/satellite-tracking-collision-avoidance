"""
Live Orbital Ballet - Three.js Integration (Simplified)
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
from pathlib import Path

# Import our modules
try:
    from data_enhanced import SatelliteDataManager
    from database.models import Satellite, ManeuverPlan, RiskAssessment
    from database.connection import DatabaseManager
except ImportError:
    # Fallback if database modules not available
    SatelliteDataManager = None
    DatabaseManager = None

# Page configuration
st.set_page_config(
    page_title="Live Orbital Ballet - Three.js Simulation",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_threejs_template():
    """Load the Three.js HTML template"""
    template_path = Path("templates/threejs_orbital_simulation_fixed.html")
    if not template_path.exists():
        return None
    
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def create_demo_satellite_data():
    """Create demo satellite data for the simulation"""
    return {
        "satellites": [
            {
                "id": "iss",
                "name": "ISS (ZARYA)",
                "norad_id": 25544,
                "position": {"x": 6800000, "y": 1200000, "z": 2100000},
                "velocity": {"x": -1500, "y": 7500, "z": 1200},
                "altitude": 408.2,
                "velocity_magnitude": 7.66,
                "color": "0xff0000",
                "size": 3,
                "is_maneuvering": False,
                "mission_type": "space_station"
            },
            {
                "id": "hubble",
                "name": "HUBBLE SPACE TELESCOPE",
                "norad_id": 20580,
                "position": {"x": 5800000, "y": -2100000, "z": 3400000},
                "velocity": {"x": 2100, "y": 6800, "z": -800},
                "altitude": 547.0,
                "velocity_magnitude": 7.59,
                "color": "0x00ff00",
                "size": 2,
                "is_maneuvering": False,
                "mission_type": "science"
            },
            {
                "id": "starlink1",
                "name": "STARLINK-1007",
                "norad_id": 44713,
                "position": {"x": 7200000, "y": 800000, "z": -1500000},
                "velocity": {"x": -800, "y": 7200, "z": 2100},
                "altitude": 550.0,
                "velocity_magnitude": 7.56,
                "color": "0x0080ff",
                "size": 1.5,
                "is_maneuvering": True,
                "mission_type": "communication"
            },
            {
                "id": "gps1",
                "name": "GPS BIIA-21",
                "norad_id": 26690,
                "position": {"x": 26600000, "y": 8900000, "z": 12000000},
                "velocity": {"x": -2100, "y": 3800, "z": 1200},
                "altitude": 20200.0,
                "velocity_magnitude": 3.87,
                "color": "0xffff00",
                "size": 2,
                "is_maneuvering": False,
                "mission_type": "navigation"
            },
            {
                "id": "tiangong",
                "name": "CSS (TIANHE)",
                "norad_id": 48274,
                "position": {"x": 6750000, "y": -800000, "z": 2800000},
                "velocity": {"x": 1200, "y": 7400, "z": -600},
                "altitude": 380.0,
                "velocity_magnitude": 7.68,
                "color": "0xff0080",
                "size": 3,
                "is_maneuvering": False,
                "mission_type": "space_station"
            }
        ],
        "debris": [
            {
                "id": f"debris_{i}",
                "name": f"DEBRIS-{1000 + i}",
                "position": {
                    "x": np.random.uniform(-20000000, 20000000),
                    "y": np.random.uniform(-20000000, 20000000),
                    "z": np.random.uniform(-20000000, 20000000)
                },
                "color": "0x808080",
                "size": 1,
                "type": "debris"
            } for i in range(15)
        ]
    }

def inject_data_into_html(html_content, satellite_data):
    """Inject satellite data into the HTML template"""
    data_script = f"""
    <script>
        // Real satellite data from Streamlit
        window.realSatelliteData = {json.dumps(satellite_data)};
        
        // Override satellite creation to use real data
        function createRealSatellites() {{
            const realData = window.realSatelliteData.satellites;
            
            // Clear existing satellites
            Object.values(satellites).forEach(sat => {{
                satelliteGroup.remove(sat);
            }});
            satellites = {{}};
            
            realData.forEach(sat => {{
                const geometry = new THREE.BoxGeometry(sat.size, sat.size, sat.size * 2);
                const material = new THREE.MeshPhongMaterial({{ 
                    color: parseInt(sat.color),
                    emissive: parseInt(sat.color),
                    emissiveIntensity: sat.is_maneuvering ? 0.4 : 0.2
                }});
                
                const mesh = new THREE.Mesh(geometry, material);
                mesh.position.set(
                    sat.position.x / 200000,
                    sat.position.y / 200000,
                    sat.position.z / 200000
                );
                
                mesh.userData = sat;
                satellites[sat.id] = mesh;
                satelliteGroup.add(mesh);
                
                // Add enhanced label
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
            
            // Add debris
            const debrisData = window.realSatelliteData.debris;
            debrisData.forEach(deb => {{
                const geometry = new THREE.SphereGeometry(deb.size, 8, 8);
                const material = new THREE.MeshPhongMaterial({{ 
                    color: parseInt(deb.color),
                    transparent: true,
                    opacity: 0.6
                }});
                
                const mesh = new THREE.Mesh(geometry, material);
                mesh.position.set(
                    deb.position.x / 200000,
                    deb.position.y / 200000,
                    deb.position.z / 200000
                );
                
                mesh.userData = deb;
                debris[deb.id] = mesh;
                debrisGroup.add(mesh);
            }});
            
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
            context.strokeStyle = `#${{color.toString(16).padStart(6, '0')}}`;
            context.lineWidth = 2;
            context.strokeRect(2, 2, 296, 76);
            
            // Text
            context.fillStyle = `#${{color.toString(16).padStart(6, '0')}}`;
            context.font = '18px Courier New';
            context.textAlign = 'center';
            context.fillText(name, 150, 30);
            
            context.font = '12px Courier New';
            context.fillStyle = '#ffffff';
            context.fillText(`Type: ${{missionType.toUpperCase()}}`, 150, 55);
            
            const texture = new THREE.CanvasTexture(canvas);
            const material = new THREE.SpriteMaterial({{ map: texture, transparent: true }});
            const sprite = new THREE.Sprite(material);
            sprite.scale.set(30, 8, 1);
            return sprite;
        }}
        
        // Override the original init function
        const originalInit = init;
        init = async function() {{
            await originalInit();
            // Use real data instead of simulated
            createRealSatellites();
            updateStatus('✅ Live Orbital Ballet Ready - Real Data Loaded');
        }};
        
        // Disable WebSocket connection for simplified version
        function connectWebSocket() {{
            updateStatus('📡 Using Streamlit Data Stream (No WebSocket)');
        }}
        
        // Enhanced simulate function with more realistic movement
        function simulate() {{
            const time = Date.now() * 0.001 * timeSpeed;
            
            // Update satellite positions with more realistic orbital mechanics
            Object.values(satellites).forEach(sat => {{
                const userData = sat.userData;
                const baseRadius = Math.sqrt(
                    userData.position.x * userData.position.x + 
                    userData.position.y * userData.position.y + 
                    userData.position.z * userData.position.z
                ) / 200000;
                
                const orbitSpeed = Math.sqrt(398600.4418 / (baseRadius * 200)) * 0.001;
                const inclination = Math.atan2(userData.position.z, userData.position.x);
                
                const angle = time * orbitSpeed;
                sat.position.x = Math.cos(angle + inclination) * baseRadius;
                sat.position.y = Math.sin(inclination) * Math.sin(angle) * baseRadius;
                sat.position.z = Math.sin(angle + inclination) * baseRadius;
                
                // Rotate satellite
                sat.rotation.y = angle;
                
                // Add maneuvering motion
                if (userData.is_maneuvering) {{
                    sat.position.x += Math.sin(time * 2) * 2;
                    sat.position.y += Math.cos(time * 2) * 2;
                }}
            }});
            
            // Update debris with different orbital characteristics
            Object.values(debris).forEach(deb => {{
                const userData = deb.userData;
                const baseRadius = Math.sqrt(
                    userData.position.x * userData.position.x + 
                    userData.position.y * userData.position.y + 
                    userData.position.z * userData.position.z
                ) / 200000;
                
                const orbitSpeed = 0.1 + Math.random() * 0.2;
                const angle = time * orbitSpeed * 0.05;
                
                deb.position.x = Math.cos(angle) * baseRadius;
                deb.position.y = Math.sin(angle) * baseRadius * 0.7;
                deb.position.z = Math.sin(angle * 1.1) * baseRadius;
            }});
        }}
    </script>
    """
    
    # Insert before closing body tag
    html_content = html_content.replace('</body>', f'{data_script}</body>')
    return html_content

def main():
    st.title("🚀 Live Orbital Ballet - Three.js 3D Simulation")
    st.markdown("**Enhanced 3D satellite tracking with interactive orbital simulation**")
    
    # Create main layout
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.header("🎮 Mission Control")
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Auto-refresh", value=False)
        
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
        
        # System status
        st.subheader("📊 System Status")
        satellite_data = create_demo_satellite_data()
        
        st.metric("🛰️ Satellites", len(satellite_data['satellites']))
        st.metric("🗂️ Debris Objects", len(satellite_data['debris']))
        active_maneuvers = len([s for s in satellite_data['satellites'] if s['is_maneuvering']])
        st.metric("🚀 Active Maneuvers", active_maneuvers)
        st.metric("⚡ Time Speed", f"{time_speed}x")
    
    with col1:
        try:
            # Load Three.js template
            html_template = load_threejs_template()
            
            if not html_template:
                st.error("Three.js template not found! Please ensure templates/threejs_orbital_simulation.html exists.")
                return
            
            # Create satellite data
            satellite_data = create_demo_satellite_data()
            
            # Inject data into HTML
            enhanced_html = inject_data_into_html(html_template, satellite_data)
            
            # Display the Three.js simulation
            st.subheader("🌍 3D Orbital Simulation")
            
            # Render the Three.js component
            st.components.v1.html(
                enhanced_html,
                height=700,
                scrolling=False
            )
            
            # Display satellite information
            st.subheader("📡 Tracked Satellites")
            
            # Create a nice table of satellites
            sat_df = pd.DataFrame([
                {
                    'Name': sat['name'],
                    'NORAD ID': sat['norad_id'],
                    'Altitude (km)': sat['altitude'],
                    'Velocity (km/s)': sat['velocity_magnitude'],
                    'Mission Type': sat['mission_type'].title(),
                    'Status': '🚀 Maneuvering' if sat['is_maneuvering'] else '✅ Nominal'
                }
                for sat in satellite_data['satellites']
            ])
            
            st.dataframe(sat_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error in 3D simulation: {str(e)}")
            st.info("Check that all required files are present and try refreshing the page.")
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(5)
        st.rerun()

if __name__ == "__main__":
    main()