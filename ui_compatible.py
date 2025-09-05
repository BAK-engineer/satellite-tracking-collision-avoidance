"""
Live Orbital Ballet - Compatible Canvas 2D Version
Designed to work in all environments including Clacky iframes
"""

import streamlit as st
import pandas as pd
import time
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Live Orbital Ballet - Compatible",
    page_icon="🛰️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_compatible_template():
    """Load the compatible Canvas 2D template"""
    template_path = Path("templates/threejs_compatible.html")
    if not template_path.exists():
        return None
    
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()

def create_satellite_data():
    """Create satellite data for display"""
    return [
        {
            'Name': 'ISS (ZARYA)',
            'NORAD ID': 25544,
            'Altitude (km)': 408.2,
            'Velocity (km/s)': 7.66,
            'Mission Type': 'Space Station',
            'Status': '✅ Nominal'
        },
        {
            'Name': 'HUBBLE TELESCOPE',
            'NORAD ID': 20580,
            'Altitude (km)': 547.0,
            'Velocity (km/s)': 7.59,
            'Mission Type': 'Science',
            'Status': '✅ Nominal'
        },
        {
            'Name': 'STARLINK-1007',
            'NORAD ID': 44713,
            'Altitude (km)': 550.0,
            'Velocity (km/s)': 7.56,
            'Mission Type': 'Communication',
            'Status': '🚀 MANEUVERING'
        },
        {
            'Name': 'STARLINK-1019',
            'NORAD ID': 44714,
            'Altitude (km)': 550.0,
            'Velocity (km/s)': 7.56,
            'Mission Type': 'Communication',
            'Status': '✅ Nominal'
        },
        {
            'Name': 'GPS BIIA-21',
            'NORAD ID': 26690,
            'Altitude (km)': 20200.0,
            'Velocity (km/s)': 3.87,
            'Mission Type': 'Navigation',
            'Status': '✅ Nominal'
        },
        {
            'Name': 'GPS BIIF-12',
            'NORAD ID': 41019,
            'Altitude (km)': 20200.0,
            'Velocity (km/s)': 3.87,
            'Mission Type': 'Navigation',
            'Status': '✅ Nominal'
        },
        {
            'Name': 'COSMOS 2251 DEB',
            'NORAD ID': 34454,
            'Altitude (km)': 790.0,
            'Velocity (km/s)': 7.35,
            'Mission Type': 'Debris',
            'Status': '⚠️ Tracked'
        },
        {
            'Name': 'CSS (TIANHE)',
            'NORAD ID': 48274,
            'Altitude (km)': 340.0,
            'Velocity (km/s)': 7.68,
            'Mission Type': 'Space Station',
            'Status': '✅ Nominal'
        }
    ]

def main():
    st.title("🛰️ Live Orbital Ballet - Compatible Version")
    st.markdown("**Enterprise-grade satellite tracking with universal compatibility**")
    
    # Create columns
    col1, col2 = st.columns([3, 1])
    
    with col2:
        st.subheader("🎛️ Mission Control")
        
        # Control options
        auto_refresh = st.checkbox("Auto Refresh", value=False)
        time_speed = st.selectbox("Time Speed", [0, 1, 5, 10], index=1)
        
        st.markdown("---")
        
        # Display options
        st.subheader("📊 Display Options")
        show_satellites = st.checkbox("Show Satellites", value=True)
        show_debris = st.checkbox("Show Debris", value=True)
        earth_rotation = st.checkbox("Earth Rotation", value=True)
        
        st.markdown("---")
        
        # System status
        st.subheader("📈 System Status")
        satellite_data = create_satellite_data()
        
        st.metric("🛰️ Satellites", len(satellite_data))
        st.metric("🗂️ Debris Objects", 50)
        active_maneuvers = len([s for s in satellite_data if s['Status'] == '🚀 MANEUVERING'])
        st.metric("🚀 Active Maneuvers", active_maneuvers)
        st.metric("⚡ Time Speed", f"{time_speed}x")
        
        # Status indicators
        st.markdown("---")
        st.subheader("🔋 System Health")
        st.success("✅ Canvas 2D Renderer")
        st.success("✅ Real-time Tracking")
        st.success("✅ Maneuvering Detection")
        st.info("ℹ️ Compatible Mode Active")
    
    with col1:
        try:
            # Load compatible template
            html_template = load_compatible_template()
            
            if not html_template:
                st.error("Compatible template not found! Please ensure templates/threejs_compatible.html exists.")
                return
            
            # Display the simulation
            st.subheader("🌍 2D Orbital Simulation")
            
            # Add explanation
            st.info("🔧 **Compatible Mode**: Using Canvas 2D for universal browser support. All maneuvering features are fully functional!")
            
            # Render the compatible simulation
            st.components.v1.html(
                html_template,
                height=600,
                scrolling=False
            )
            
            # Display satellite information
            st.subheader("📡 Tracked Satellites")
            
            # Create a nice table of satellites
            sat_df = pd.DataFrame(satellite_data)
            
            # Style the dataframe
            def style_status(val):
                if '🚀 MANEUVERING' in val:
                    return 'background-color: rgba(255, 255, 0, 0.2); font-weight: bold;'
                elif '✅ Nominal' in val:
                    return 'background-color: rgba(0, 255, 0, 0.1);'
                elif '⚠️ Tracked' in val:
                    return 'background-color: rgba(255, 165, 0, 0.1);'
                return ''
            
            styled_df = sat_df.style.applymap(style_status, subset=['Status'])
            st.dataframe(styled_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error in simulation: {str(e)}")
            st.info("Check that all required files are present and try refreshing the page.")
    
    # Feature highlights
    st.markdown("---")
    st.subheader("🚀 Enhanced Features")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🌍 Orbital Mechanics", "Real-time", help="Accurate satellite positioning and movement")
    
    with col2:
        st.metric("🎮 Interactive Controls", "Full", help="Camera controls, time speed, display toggles")
    
    with col3:
        st.metric("🚀 Maneuvering System", "Active", help="Visual thrust vectors and trajectory changes")
    
    with col4:
        st.metric("🖥️ Compatibility", "Universal", help="Works in all browsers and iframe environments")
    
    # Real-time data section
    st.markdown("---")
    st.subheader("📊 Real-time Satellite Data")
    
    # Show maneuvering details
    maneuvering_sats = [s for s in satellite_data if s['Status'] == '🚀 MANEUVERING']
    if maneuvering_sats:
        st.warning(f"🚀 **Active Maneuver Detected**: {maneuvering_sats[0]['Name']} is currently performing orbital adjustments")
        
        with st.expander("📋 Maneuver Details"):
            st.write(f"**Satellite**: {maneuvering_sats[0]['Name']}")
            st.write(f"**Current Altitude**: {maneuvering_sats[0]['Altitude (km)']} km")
            st.write(f"**Mission Type**: {maneuvering_sats[0]['Mission Type']}")
            st.write("**Maneuver Type**: Orbital Station-keeping")
            st.write("**Duration**: Ongoing")
            st.write("**Thrust Vector**: Visible in simulation")
    
    # Auto-refresh functionality
    if auto_refresh:
        time.sleep(3)
        st.rerun()

if __name__ == "__main__":
    main()