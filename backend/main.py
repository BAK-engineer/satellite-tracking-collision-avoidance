"""
ORBITAL NEXUS - Professional Satellite Tracking Backend
FastAPI + WebSockets + PostgreSQL + Real-time TLE Data
"""

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uvicorn
from contextlib import asynccontextmanager

# Database
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from databases import Database
import os

# Orbital mechanics
import numpy as np
from sgp4.api import Satrec
from sgp4 import exporter
import requests

# Configuration
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/orbital_nexus")
CELESTRAK_BASE_URL = "https://celestrak.org"

# Database setup
database = Database(DATABASE_URL)
engine = create_engine(DATABASE_URL.replace("postgresql://", "postgresql://"))
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class Satellite(Base):
    __tablename__ = "satellites"
    
    id = Column(Integer, primary_key=True, index=True)
    norad_id = Column(Integer, unique=True, index=True)
    name = Column(String, index=True)
    tle_line1 = Column(Text)
    tle_line2 = Column(Text)
    mission_type = Column(String, default="unknown")
    is_active = Column(Boolean, default=True)
    is_maneuvering = Column(Boolean, default=False)
    last_updated = Column(DateTime, default=datetime.utcnow)
    altitude = Column(Float)
    inclination = Column(Float)
    eccentricity = Column(Float)

class TelemetryData(Base):
    __tablename__ = "telemetry"
    
    id = Column(Integer, primary_key=True, index=True)
    satellite_id = Column(Integer, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    position_x = Column(Float)
    position_y = Column(Float)
    position_z = Column(Float)
    velocity_x = Column(Float)
    velocity_y = Column(Float)
    velocity_z = Column(Float)
    altitude = Column(Float)

# Create tables
Base.metadata.create_all(bind=engine)

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket Manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.satellite_data_cache: Dict = {}
        
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Client connected. Total connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"Client disconnected. Total connections: {len(self.active_connections)}")
        
    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            self.disconnect(websocket)
            
    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Orbital mechanics helper
class OrbitalCalculator:
    @staticmethod
    def tle_to_position(tle_line1: str, tle_line2: str, timestamp: datetime = None) -> Dict:
        """Convert TLE to current position using SGP4"""
        try:
            satellite = Satrec.twoline2rv(tle_line1, tle_line2)
            
            if timestamp is None:
                timestamp = datetime.utcnow()
            
            # Convert to Julian date
            jd = timestamp.toordinal() + 1721425.5
            fr = (timestamp.hour + timestamp.minute/60.0 + timestamp.second/3600.0) / 24.0
            
            # Get position and velocity
            error, position, velocity = satellite.sgp4(jd, fr)
            
            if error != 0:
                logger.warning(f"SGP4 error code: {error}")
                return None
                
            # Convert to kilometers and km/s
            pos = [p for p in position]  # Already in km
            vel = [v for v in velocity]  # Already in km/s
            
            # Calculate altitude (distance from Earth center - Earth radius)
            earth_radius = 6371.0  # km
            altitude = np.sqrt(sum(p**2 for p in pos)) - earth_radius
            
            return {
                "position": pos,
                "velocity": vel,
                "altitude": altitude,
                "timestamp": timestamp.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error calculating position: {e}")
            return None

    @staticmethod
    def detect_maneuvering(satellite_id: int, db: Session) -> bool:
        """Detect if satellite is maneuvering based on velocity changes"""
        try:
            # Get recent telemetry data
            recent_data = db.query(TelemetryData).filter(
                TelemetryData.satellite_id == satellite_id,
                TelemetryData.timestamp > datetime.utcnow() - timedelta(hours=1)
            ).order_by(TelemetryData.timestamp.desc()).limit(10).all()
            
            if len(recent_data) < 5:
                return False
                
            # Calculate velocity magnitudes
            velocities = []
            for data in recent_data:
                vel_mag = np.sqrt(data.velocity_x**2 + data.velocity_y**2 + data.velocity_z**2)
                velocities.append(vel_mag)
            
            # Check for significant velocity changes (simple threshold)
            vel_std = np.std(velocities)
            return vel_std > 0.1  # km/s threshold for maneuvering detection
            
        except Exception as e:
            logger.error(f"Error detecting maneuvering: {e}")
            return False

# Data fetching
class SatelliteDataManager:
    def __init__(self):
        self.calculator = OrbitalCalculator()
        
    async def fetch_tle_data(self) -> List[Dict]:
        """Fetch TLE data from Celestrak"""
        categories = [
            "stations",  # Space stations
            "visual",    # Bright satellites
            "active",    # Active satellites
            "starlink",  # Starlink constellation
        ]
        
        all_satellites = []
        
        for category in categories:
            try:
                url = f"{CELESTRAK_BASE_URL}/NORAD/elements/gp.php?GROUP={category}&FORMAT=tle"
                response = requests.get(url, timeout=30)
                
                if response.status_code == 200:
                    tle_data = response.text.strip().split('\n')
                    
                    # Parse TLE data
                    for i in range(0, len(tle_data), 3):
                        if i + 2 < len(tle_data):
                            name = tle_data[i].strip()
                            line1 = tle_data[i + 1].strip()
                            line2 = tle_data[i + 2].strip()
                            
                            if line1.startswith('1') and line2.startswith('2'):
                                try:
                                    norad_id = int(line1[2:7])
                                    all_satellites.append({
                                        "name": name,
                                        "norad_id": norad_id,
                                        "tle_line1": line1,
                                        "tle_line2": line2,
                                        "category": category
                                    })
                                except ValueError:
                                    continue
                                    
            except Exception as e:
                logger.error(f"Error fetching TLE data for {category}: {e}")
                continue
        
        return all_satellites
    
    async def update_satellite_positions(self, db: Session):
        """Update positions for all tracked satellites"""
        satellites = db.query(Satellite).filter(Satellite.is_active == True).all()
        
        for satellite in satellites:
            try:
                position_data = self.calculator.tle_to_position(
                    satellite.tle_line1, 
                    satellite.tle_line2
                )
                
                if position_data:
                    # Store telemetry data
                    telemetry = TelemetryData(
                        satellite_id=satellite.norad_id,
                        position_x=position_data["position"][0],
                        position_y=position_data["position"][1],
                        position_z=position_data["position"][2],
                        velocity_x=position_data["velocity"][0],
                        velocity_y=position_data["velocity"][1],
                        velocity_z=position_data["velocity"][2],
                        altitude=position_data["altitude"]
                    )
                    db.add(telemetry)
                    
                    # Check for maneuvering
                    is_maneuvering = self.calculator.detect_maneuvering(satellite.norad_id, db)
                    if satellite.is_maneuvering != is_maneuvering:
                        satellite.is_maneuvering = is_maneuvering
                        
                    # Update satellite data
                    satellite.altitude = position_data["altitude"]
                    satellite.last_updated = datetime.utcnow()
                    
                    # Cache for WebSocket broadcast
                    manager.satellite_data_cache[satellite.norad_id] = {
                        "id": satellite.norad_id,
                        "name": satellite.name,
                        "position": position_data["position"],
                        "velocity": position_data["velocity"],
                        "altitude": position_data["altitude"],
                        "is_maneuvering": is_maneuvering,
                        "timestamp": position_data["timestamp"]
                    }
                    
            except Exception as e:
                logger.error(f"Error updating satellite {satellite.name}: {e}")
                
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            logger.error(f"Database commit error: {e}")

# Initialize data manager
data_manager = SatelliteDataManager()

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Startup and shutdown events
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await database.connect()
    logger.info("🛰️ ORBITAL NEXUS Backend Started")
    logger.info("🌍 Connecting to Celestrak for TLE data...")
    
    # Start background tasks
    asyncio.create_task(update_satellite_data_task())
    asyncio.create_task(broadcast_satellite_positions())
    
    yield
    
    # Shutdown
    await database.disconnect()
    logger.info("🛰️ ORBITAL NEXUS Backend Stopped")

# FastAPI app
app = FastAPI(
    title="ORBITAL NEXUS API",
    description="Professional 3D Satellite Tracking Platform - Real-time orbital mechanics with SGP4 propagation",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Background tasks
async def update_satellite_data_task():
    """Background task to fetch and update satellite data"""
    while True:
        try:
            db = SessionLocal()
            
            # Fetch fresh TLE data every hour
            tle_data = await data_manager.fetch_tle_data()
            
            for sat_data in tle_data:
                existing = db.query(Satellite).filter(
                    Satellite.norad_id == sat_data["norad_id"]
                ).first()
                
                if existing:
                    # Update existing satellite
                    existing.tle_line1 = sat_data["tle_line1"]
                    existing.tle_line2 = sat_data["tle_line2"]
                    existing.last_updated = datetime.utcnow()
                else:
                    # Add new satellite
                    new_satellite = Satellite(
                        norad_id=sat_data["norad_id"],
                        name=sat_data["name"],
                        tle_line1=sat_data["tle_line1"],
                        tle_line2=sat_data["tle_line2"],
                        mission_type=sat_data["category"]
                    )
                    db.add(new_satellite)
            
            db.commit()
            db.close()
            
            logger.info(f"Updated {len(tle_data)} satellites")
            
        except Exception as e:
            logger.error(f"Error in satellite data update task: {e}")
            
        # Wait 1 hour before next update
        await asyncio.sleep(3600)

async def broadcast_satellite_positions():
    """Background task to broadcast satellite positions via WebSocket"""
    while True:
        try:
            if manager.active_connections:
                db = SessionLocal()
                await data_manager.update_satellite_positions(db)
                db.close()
                
                # Broadcast cached data
                if manager.satellite_data_cache:
                    broadcast_data = {
                        "type": "satellite_update",
                        "data": list(manager.satellite_data_cache.values()),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    await manager.broadcast(json.dumps(broadcast_data))
                    
        except Exception as e:
            logger.error(f"Error in broadcast task: {e}")
            
        # Update every 30 seconds
        await asyncio.sleep(30)

# API Routes
@app.get("/")
async def root():
    return {"message": "🛰️ ORBITAL NEXUS API v1.0.0", "status": "operational"}

@app.get("/api/v1/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "database": "connected" if database.is_connected else "disconnected",
        "active_connections": len(manager.active_connections)
    }

@app.get("/api/v1/satellites")
async def get_satellites(
    skip: int = 0, 
    limit: int = 100, 
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    query = db.query(Satellite)
    if active_only:
        query = query.filter(Satellite.is_active == True)
    
    satellites = query.offset(skip).limit(limit).all()
    
    result = []
    for sat in satellites:
        position_data = data_manager.calculator.tle_to_position(
            sat.tle_line1, sat.tle_line2
        )
        
        result.append({
            "id": sat.norad_id,
            "name": sat.name,
            "mission_type": sat.mission_type,
            "is_active": sat.is_active,
            "is_maneuvering": sat.is_maneuvering,
            "altitude": position_data["altitude"] if position_data else sat.altitude,
            "position": position_data["position"] if position_data else [0, 0, 0],
            "velocity": position_data["velocity"] if position_data else [0, 0, 0],
            "last_updated": sat.last_updated.isoformat()
        })
    
    return {"satellites": result, "total": len(result)}

@app.get("/api/v1/satellites/{satellite_id}")
async def get_satellite(satellite_id: int, db: Session = Depends(get_db)):
    satellite = db.query(Satellite).filter(Satellite.norad_id == satellite_id).first()
    
    if not satellite:
        raise HTTPException(status_code=404, detail="Satellite not found")
    
    position_data = data_manager.calculator.tle_to_position(
        satellite.tle_line1, satellite.tle_line2
    )
    
    return {
        "id": satellite.norad_id,
        "name": satellite.name,
        "mission_type": satellite.mission_type,
        "is_active": satellite.is_active,
        "is_maneuvering": satellite.is_maneuvering,
        "tle_line1": satellite.tle_line1,
        "tle_line2": satellite.tle_line2,
        "position": position_data["position"] if position_data else [0, 0, 0],
        "velocity": position_data["velocity"] if position_data else [0, 0, 0],
        "altitude": position_data["altitude"] if position_data else satellite.altitude,
        "last_updated": satellite.last_updated.isoformat()
    }

@app.get("/api/v1/satellites/{satellite_id}/telemetry")
async def get_satellite_telemetry(
    satellite_id: int, 
    hours: int = 24,
    db: Session = Depends(get_db)
):
    start_time = datetime.utcnow() - timedelta(hours=hours)
    
    telemetry = db.query(TelemetryData).filter(
        TelemetryData.satellite_id == satellite_id,
        TelemetryData.timestamp >= start_time
    ).order_by(TelemetryData.timestamp.asc()).all()
    
    return {
        "satellite_id": satellite_id,
        "telemetry": [
            {
                "timestamp": t.timestamp.isoformat(),
                "position": [t.position_x, t.position_y, t.position_z],
                "velocity": [t.velocity_x, t.velocity_y, t.velocity_z],
                "altitude": t.altitude
            } for t in telemetry
        ]
    }

@app.get("/api/v1/maneuvering")
async def get_maneuvering_satellites(db: Session = Depends(get_db)):
    maneuvering_satellites = db.query(Satellite).filter(
        Satellite.is_maneuvering == True,
        Satellite.is_active == True
    ).all()
    
    result = []
    for sat in maneuvering_satellites:
        position_data = data_manager.calculator.tle_to_position(
            sat.tle_line1, sat.tle_line2
        )
        
        result.append({
            "id": sat.norad_id,
            "name": sat.name,
            "mission_type": sat.mission_type,
            "position": position_data["position"] if position_data else [0, 0, 0],
            "velocity": position_data["velocity"] if position_data else [0, 0, 0],
            "altitude": position_data["altitude"] if position_data else sat.altitude,
            "last_updated": sat.last_updated.isoformat()
        })
    
    return {"maneuvering_satellites": result, "count": len(result)}

@app.post("/api/v1/tle/update")
async def trigger_tle_update():
    """Manually trigger TLE data update"""
    try:
        asyncio.create_task(update_satellite_data_task())
        return {"message": "TLE update triggered", "status": "success"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Update failed: {str(e)}")

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        # Send initial data
        if manager.satellite_data_cache:
            initial_data = {
                "type": "initial_data",
                "data": list(manager.satellite_data_cache.values()),
                "timestamp": datetime.utcnow().isoformat()
            }
            await manager.send_personal_message(json.dumps(initial_data), websocket)
        
        # Keep connection alive and handle messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle different message types
                if message.get("type") == "ping":
                    pong = {"type": "pong", "timestamp": datetime.utcnow().isoformat()}
                    await manager.send_personal_message(json.dumps(pong), websocket)
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                break
                
    finally:
        manager.disconnect(websocket)

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )