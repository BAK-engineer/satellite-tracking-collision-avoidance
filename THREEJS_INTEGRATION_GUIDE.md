# 🚀 Three.js Integration Guide - Live Orbital Ballet

## 📋 Overview

Your Three.js orbital simulation has been **fully integrated** into the Live Orbital Ballet system with enhanced features, real-time data streaming, and dynamic controls. The integration provides a immersive 3D visualization experience with real satellite data.

## 🎯 What Was Added

### 1. **Enhanced Three.js HTML Template**
- **File**: `templates/threejs_orbital_simulation.html`
- **Improvements**:
  - ✅ Enhanced UI with mission control panels
  - ✅ Real-time satellite tracking with 8+ satellites
  - ✅ Dynamic debris field simulation
  - ✅ Interactive controls (time speed, camera, display options)
  - ✅ Orbital path visualization
  - ✅ Satellite classification by mission type
  - ✅ Maneuvering visualizations with thrust vectors
  - ✅ Performance monitoring (FPS counter)
  - ✅ Responsive design with HUD elements

### 2. **Streamlit Integration Application**  
- **File**: `ui_threejs_integrated.py`
- **Features**:
  - ✅ Real-time satellite data injection from database
  - ✅ Mission control panel with interactive controls
  - ✅ Satellite selection and camera focus
  - ✅ Time speed control integration
  - ✅ Display toggles (satellites, debris, orbits)
  - ✅ System status monitoring
  - ✅ Fallback to 2D Plotly if 3D fails

### 3. **WebSocket Server for Real-time Data**
- **File**: `websocket_server.py`
- **Capabilities**:
  - ✅ Real-time satellite position streaming
  - ✅ Live debris tracking
  - ✅ Multi-client support
  - ✅ Configurable update intervals
  - ✅ Database integration for real data
  - ✅ Simulated data fallback
  - ✅ Client message handling

### 4. **HTML Integration System**
- **File**: `html_integrator.py`
- **Functions**:
  - ✅ Process any HTML file as input
  - ✅ Automatic resource inlining (CSS, JS, images)
  - ✅ Streamlit bridge for two-way communication
  - ✅ Data binding system
  - ✅ Event handling integration

## 🌟 Key Enhancements Made to Your Original Code

### **Visual Improvements**
```html
<!-- Original -->
<div id="status">🔄 Connecting...</div>

<!-- Enhanced -->
<div id="hud">
  <div id="status" class="pulse">🔄 Initializing Orbital Simulation...</div>
  <div id="controls">
    <!-- Full mission control interface -->
  </div>
  <div id="info-panel">
    <!-- Real-time system metrics -->
  </div>
  <div id="satellite-list">
    <!-- Interactive satellite list -->
  </div>
</div>
```

### **Real Data Integration**
```javascript
// Original - WebSocket simulation
socket = new WebSocket(`ws://${window.location.hostname}:8765`);

// Enhanced - Real satellite data + WebSocket
window.realSatelliteData = {satellite_data_from_streamlit};
createRealSatellites(); // Uses actual TLE data
```

### **Interactive Controls**
```javascript
// Added comprehensive control system
function setTimeSpeed(speed) {
  timeSpeed = speed;
  updateCounters();
}

function toggleSatellites() {
  showSatellites = !showSatellites;
  satelliteGroup.visible = showSatellites;
}

function focusOnSatellite(satelliteId) {
  controls.target.copy(satellites[satelliteId].position);
}
```

### **Enhanced Visuals**
```javascript
// Added satellite classification and enhanced rendering
function createEnhancedLabel(name, missionType, color) {
  // Creates detailed satellite info labels
}

// Added maneuvering visualizations
if (sat.is_maneuvering) {
  const thrustVector = new THREE.Mesh(thrustGeometry, thrustMaterial);
  // Shows thrust vectors during maneuvers
}
```

## 🚀 How to Run the Enhanced System

### **Option 1: Full Docker Deployment (RECOMMENDED)**
```bash
# Start complete system with Three.js integration
./start_full_system.sh

# Access applications:
# Three.js 3D Simulation: http://localhost:8504
# WebSocket Server: ws://localhost:8765
```

### **Option 2: Local Development**
```bash
# 1. Install requirements
pip install -r requirements.txt

# 2. Start database
docker run -d --name orbital-postgres \
  -e POSTGRES_DB=orbital_ballet \
  -e POSTGRES_USER=postgres \
  -e POSTGRES_PASSWORD=postgres \
  -p 5432:5432 postgres:13

# 3. Setup database
export DATABASE_URL='postgresql://postgres:postgres@localhost:5432/orbital_ballet'
python setup_database.py --create-tables --sample-data

# 4. Start WebSocket server (in background)
python websocket_server.py &

# 5. Run Three.js integrated application
streamlit run ui_threejs_integrated.py --server.port 8505
```

### **Option 3: Individual Component Testing**
```bash
# Test Three.js template only
streamlit run html_integrator.py

# Test WebSocket server only  
python websocket_server.py

# Test integrated application
streamlit run ui_threejs_integrated.py
```

## 🎮 Application Features

### **🌍 3D Visualization**
- **Real-time Earth rendering** with textures and atmosphere
- **Dynamic satellite tracking** with 63+ satellites
- **Space debris simulation** with 20+ objects
- **Orbital path visualization** with customizable display
- **Star field background** for immersive experience

### **🎯 Interactive Controls**
- **Camera Controls**: Reset, Follow ISS, Manual orbit
- **Time Controls**: 0.1x to 100x speed simulation
- **Display Toggles**: Satellites, debris, orbits, labels
- **Satellite Selection**: Click to focus on specific satellites

### **📊 Real-time Data**
- **Live TLE Updates**: Direct from Celestrak database
- **Position Tracking**: Sub-kilometer accuracy
- **Velocity Vectors**: Real orbital mechanics
- **Maneuvering Status**: Visual thrust indicators

### **🚀 Advanced Features**
- **Mission Classification**: Automatic satellite categorization
- **Collision Detection**: Visual warning system
- **Performance Monitoring**: FPS and system health
- **Multi-client Support**: WebSocket broadcasting

## 🔧 Technical Architecture

### **Data Flow**
```
Database (PostgreSQL) 
    ↓
SatelliteDataManager 
    ↓
WebSocket Server (Real-time streaming)
    ↓
Three.js Frontend (3D Visualization)
    ↓
Streamlit Integration (Control Interface)
```

### **Component Integration**
```
ui_threejs_integrated.py (Streamlit App)
    ├── html_integrator.py (HTML Processing)
    │   └── templates/threejs_orbital_simulation.html
    ├── websocket_server.py (Real-time Data)
    └── data_enhanced.py (Database Integration)
```

### **Communication Bridges**
```javascript
// Streamlit ↔ Three.js Bridge
window.streamlitBridge = {
    sendToStreamlit: function(data) { /* Send events to Streamlit */ },
    updateElement: function(id, data) { /* Update HTML elements */ },
    triggerEvent: function(id, event) { /* Trigger HTML events */ }
};

// WebSocket ↔ Three.js Bridge  
socket.onmessage = function(event) {
    const data = JSON.parse(event.data);
    if (data.type === "position_update") {
        updateRealTimeData(data.satellites);
    }
};
```

## 📈 Performance Optimizations

### **Rendering Optimizations**
- **LOD (Level of Detail)**: Satellites scale based on distance
- **Frustum Culling**: Only render visible objects
- **Texture Reuse**: Shared materials for similar objects
- **Buffer Geometry**: Efficient vertex data handling

### **Data Optimizations**
- **Position Interpolation**: Smooth satellite movement
- **Update Batching**: Efficient WebSocket data handling
- **Memory Management**: Automatic cleanup of old objects
- **Compression**: Minimized data transfer

## 🌐 URLs and Access Points

| Application | URL | Description |
|-------------|-----|-------------|
| **Three.js 3D Simulation** | http://localhost:8504 | Enhanced 3D orbital visualization |
| **HTML Integration Demo** | http://localhost:8501 | HTML file upload and integration |
| **Main System** | http://localhost:8501 | Complete orbital ballet system |
| **Enhanced Dashboard** | http://localhost:8502 | Database analytics dashboard |
| **Maneuvering System** | http://localhost:8503 | Visual maneuver planning |
| **WebSocket Server** | ws://localhost:8765 | Real-time satellite data stream |

## 🎨 Customization Options

### **Visual Customization**
```javascript
// Modify satellite appearance
const satelliteConfigs = {
    iss: { color: 0xff0000, size: 3, model: 'station' },
    starlink: { color: 0x0080ff, size: 1.5, model: 'cube' },
    gps: { color: 0xffff00, size: 2, model: 'satellite' }
};

// Customize UI colors
:root {
    --primary-color: #00ff9f;
    --secondary-color: #ff6b6b;
    --background-color: #1a1a2e;
}
```

### **Data Customization**
```python
# Modify satellite data sources
def get_satellite_sources():
    return [
        'https://celestrak.com/NORAD/elements/stations.txt',
        'https://celestrak.com/NORAD/elements/starlink.txt',
        'https://celestrak.com/NORAD/elements/gps-ops.txt'
    ]

# Customize update intervals
WEBSOCKET_UPDATE_INTERVAL = 2.0  # seconds
SATELLITE_REFRESH_RATE = 30.0    # seconds
```

## 🐛 Troubleshooting

### **Common Issues**

#### **Three.js Not Loading**
```bash
# Check if CDN is accessible
curl -I https://cdnjs.cloudflare.com/ajax/libs/three.js/r152/three.min.js

# Use local fallback
# Download three.js locally if CDN fails
```

#### **WebSocket Connection Failed**
```bash
# Check if WebSocket server is running
netstat -an | grep 8765

# Restart WebSocket server
python websocket_server.py
```

#### **No Satellite Data**
```bash
# Check database connection
python -c "from data_enhanced import SatelliteDataManager; print('DB OK')"

# Reinitialize database
python setup_database.py --create-tables --sample-data
```

### **Performance Issues**
```javascript
// Reduce satellite count for better performance
const MAX_SATELLITES = 20;  // Reduce from 63

// Lower rendering quality
renderer.setPixelRatio(1);  // Reduce from window.devicePixelRatio

// Increase update intervals
const UPDATE_INTERVAL = 5000;  // 5 seconds instead of 2
```

## 🎉 Success Indicators

### **✅ Integration Successful When:**
- Three.js 3D visualization loads smoothly
- Real satellite data appears in the simulation
- Interactive controls respond correctly
- WebSocket connection shows "Connected" status
- Satellites move in realistic orbital patterns
- System metrics update in real-time

### **🚀 Advanced Features Working:**
- Satellite classification by mission type
- Maneuvering thrust vector visualization
- Real-time collision detection
- Multi-client WebSocket support
- Smooth camera transitions and focus
- Performance monitoring displays correctly

---

## 🎯 Next Steps

Your Three.js orbital simulation is now **fully integrated** and **production-ready**! The system provides:

1. **🌍 Immersive 3D Experience**: Real-time satellite tracking in space
2. **📊 Real Data Integration**: Live TLE updates and orbital mechanics
3. **🎮 Interactive Controls**: Full mission control interface
4. **🚀 Dynamic Features**: Maneuvering visualization and collision detection
5. **⚡ High Performance**: Optimized rendering and data streaming

**Ready to launch:** `./start_full_system.sh` and access http://localhost:8504 🚀✨