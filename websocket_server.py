"""
WebSocket Server for Real-time Satellite Data
Provides live data stream for the Three.js orbital simulation
"""

import asyncio
import websockets
import json
import time
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Any
import threading
from data_enhanced import SatelliteDataManager
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OrbitalWebSocketServer:
    """Real-time WebSocket server for satellite orbital data"""
    
    def __init__(self, host='localhost', port=8765):
        self.host = host
        self.port = port
        self.clients = set()
        self.data_manager = None
        self.running = False
        self.update_interval = 2.0  # seconds
        
        # Initialize data manager if database is available
        try:
            DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/orbital_ballet')
            self.data_manager = SatelliteDataManager(DATABASE_URL)
            logger.info("Connected to database for real satellite data")
        except Exception as e:
            logger.warning(f"Database connection failed: {e}. Using simulated data.")
            self.data_manager = None
    
    async def register_client(self, websocket, path):
        """Register a new WebSocket client"""
        self.clients.add(websocket)
        logger.info(f"Client connected. Total clients: {len(self.clients)}")
        
        try:
            # Send initial data
            await self.send_initial_data(websocket)
            
            # Keep connection alive and handle client messages
            async for message in websocket:
                try:
                    data = json.loads(message)
                    await self.handle_client_message(websocket, data)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON received: {message}")
                except Exception as e:
                    logger.error(f"Error handling client message: {e}")
                    
        except websockets.exceptions.ConnectionClosed:
            logger.info("Client disconnected")
        except Exception as e:
            logger.error(f"Error in client handler: {e}")
        finally:
            self.clients.discard(websocket)
            logger.info(f"Client removed. Total clients: {len(self.clients)}")
    
    async def send_initial_data(self, websocket):
        """Send initial satellite data to a new client"""
        try:
            satellite_data = await self.get_current_satellite_data()
            initial_message = {
                "type": "initial_data",
                "timestamp": datetime.now().isoformat(),
                "satellites": satellite_data["satellites"],
                "debris": satellite_data["debris"],
                "system_info": {
                    "server_time": datetime.now().isoformat(),
                    "update_interval": self.update_interval,
                    "data_source": "live" if self.data_manager else "simulated"
                }
            }
            await websocket.send(json.dumps(initial_message))
            logger.info("Initial data sent to client")
        except Exception as e:
            logger.error(f"Error sending initial data: {e}")
    
    async def handle_client_message(self, websocket, data):
        """Handle messages from clients"""
        message_type = data.get("type", "")
        
        if message_type == "request_update":
            # Client requesting immediate data update
            satellite_data = await self.get_current_satellite_data()
            response = {
                "type": "position_update",
                "timestamp": datetime.now().isoformat(),
                "satellites": satellite_data["satellites"],
                "debris": satellite_data["debris"]
            }
            await websocket.send(json.dumps(response))
            
        elif message_type == "set_update_interval":
            # Client requesting to change update interval
            new_interval = data.get("interval", self.update_interval)
            if 0.5 <= new_interval <= 60:  # Reasonable bounds
                self.update_interval = new_interval
                logger.info(f"Update interval changed to {new_interval} seconds")
            
        elif message_type == "client_info":
            # Client sending information about itself
            logger.info(f"Client info: {data.get('info', 'No info provided')}")
    
    async def get_current_satellite_data(self):
        """Get current satellite positions and data"""
        try:
            if self.data_manager:
                # Use real satellite data
                satellites_df = self.data_manager.get_current_positions()
                
                if not satellites_df.empty:
                    satellites = []
                    for _, sat in satellites_df.iterrows():
                        satellites.append({
                            "id": f"sat_{sat['satellite_id']}",
                            "name": sat['name'],
                            "norad_id": sat.get('satellite_id', 0),
                            "position": [float(sat['x']), float(sat['y']), float(sat['z'])],
                            "velocity": [
                                float(sat.get('vx', 0)),
                                float(sat.get('vy', 0)),
                                float(sat.get('vz', 0))
                            ],
                            "altitude": float(sat['altitude']),
                            "velocity_magnitude": float(sat['velocity']),
                            "is_maneuvering": sat.get('is_maneuvering', False),
                            "mission_type": self.classify_satellite_mission(sat['name']),
                            "last_updated": datetime.now().isoformat()
                        })
                    
                    return {
                        "satellites": satellites,
                        "debris": self.generate_simulated_debris(20)
                    }
            
            # Fallback to simulated data
            return self.generate_simulated_data()
            
        except Exception as e:
            logger.error(f"Error getting satellite data: {e}")
            return self.generate_simulated_data()
    
    def classify_satellite_mission(self, name):
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
    
    def generate_simulated_data(self):
        """Generate simulated satellite data for demo purposes"""
        current_time = time.time()
        
        satellites = []
        satellite_configs = [
            {"id": "iss", "name": "ISS (ZARYA)", "radius": 6800, "speed": 0.8, "color": "red"},
            {"id": "hubble", "name": "HUBBLE SPACE TELESCOPE", "radius": 7100, "speed": 0.6, "color": "green"},
            {"id": "starlink1", "name": "STARLINK-1007", "radius": 6900, "speed": 0.9, "color": "blue"},
            {"id": "starlink2", "name": "STARLINK-1019", "radius": 6950, "speed": 0.85, "color": "blue"},
            {"id": "gps1", "name": "GPS BIIA-21", "radius": 26600, "speed": 0.3, "color": "yellow"},
            {"id": "gps2", "name": "GPS BIIF-12", "radius": 26550, "speed": 0.32, "color": "yellow"},
            {"id": "tiangong", "name": "CSS (TIANHE)", "radius": 6750, "speed": 0.75, "color": "magenta"}
        ]
        
        for config in satellite_configs:
            # Calculate orbital position
            angle = (current_time * config["speed"] * 0.1) % (2 * np.pi)
            inclination = np.random.uniform(-0.5, 0.5)  # Random inclination
            
            # Convert to Cartesian coordinates (in km)
            x = config["radius"] * np.cos(angle) * 1000
            y = config["radius"] * np.sin(angle) * np.cos(inclination) * 1000
            z = config["radius"] * np.sin(angle) * np.sin(inclination) * 1000
            
            # Calculate velocity (simplified)
            orbital_velocity = np.sqrt(398600.4418 / config["radius"])  # km/s
            vx = -orbital_velocity * np.sin(angle) * 1000
            vy = orbital_velocity * np.cos(angle) * np.cos(inclination) * 1000
            vz = orbital_velocity * np.cos(angle) * np.sin(inclination) * 1000
            
            satellites.append({
                "id": config["id"],
                "name": config["name"],
                "position": [x, y, z],
                "velocity": [vx, vy, vz],
                "altitude": config["radius"] - 6371,  # Earth radius
                "velocity_magnitude": orbital_velocity,
                "is_maneuvering": np.random.random() < 0.1,  # 10% chance of maneuvering
                "mission_type": self.classify_satellite_mission(config["name"]),
                "last_updated": datetime.now().isoformat()
            })
        
        return {
            "satellites": satellites,
            "debris": self.generate_simulated_debris(30)
        }
    
    def generate_simulated_debris(self, count):
        """Generate simulated space debris"""
        debris = []
        current_time = time.time()
        
        for i in range(count):
            # Random orbital parameters
            radius = np.random.uniform(6500, 12000)  # km
            angle = (current_time * np.random.uniform(0.1, 1.0) + i) % (2 * np.pi)
            inclination = np.random.uniform(-1, 1)
            
            # Position
            x = radius * np.cos(angle) * 1000
            y = radius * np.sin(angle) * np.cos(inclination) * 1000
            z = radius * np.sin(angle) * np.sin(inclination) * 1000
            
            debris.append({
                "id": f"debris_{i}",
                "name": f"DEBRIS-{1000 + i}",
                "position": [x, y, z],
                "size": np.random.uniform(0.5, 2.0),
                "type": "debris",
                "last_updated": datetime.now().isoformat()
            })
        
        return debris
    
    async def broadcast_updates(self):
        """Broadcast position updates to all connected clients"""
        while self.running:
            try:
                if self.clients:
                    satellite_data = await self.get_current_satellite_data()
                    message = {
                        "type": "position_update",
                        "timestamp": datetime.now().isoformat(),
                        "satellites": satellite_data["satellites"],
                        "debris": satellite_data["debris"]
                    }
                    
                    # Send to all connected clients
                    disconnected_clients = set()
                    for client in self.clients:
                        try:
                            await client.send(json.dumps(message))
                        except websockets.exceptions.ConnectionClosed:
                            disconnected_clients.add(client)
                        except Exception as e:
                            logger.error(f"Error sending to client: {e}")
                            disconnected_clients.add(client)
                    
                    # Remove disconnected clients
                    self.clients -= disconnected_clients
                    
                    if self.clients:
                        logger.debug(f"Broadcast update to {len(self.clients)} clients")
                
                await asyncio.sleep(self.update_interval)
                
            except Exception as e:
                logger.error(f"Error in broadcast loop: {e}")
                await asyncio.sleep(1)
    
    async def start_server(self):
        """Start the WebSocket server"""
        self.running = True
        logger.info(f"Starting WebSocket server on {self.host}:{self.port}")
        
        # Start broadcast task
        broadcast_task = asyncio.create_task(self.broadcast_updates())
        
        try:
            # Start WebSocket server
            server = await websockets.serve(
                self.register_client,
                self.host,
                self.port,
                ping_interval=20,
                ping_timeout=10
            )
            
            logger.info(f"WebSocket server running on ws://{self.host}:{self.port}")
            
            # Keep server running
            await server.wait_closed()
            
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            self.running = False
            broadcast_task.cancel()
            logger.info("WebSocket server stopped")
    
    def start_in_thread(self):
        """Start the WebSocket server in a separate thread"""
        def run_server():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                loop.run_until_complete(self.start_server())
            except KeyboardInterrupt:
                logger.info("Server interrupted by user")
            finally:
                loop.close()
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        logger.info("WebSocket server started in background thread")
        return server_thread

def main():
    """Main function to run the WebSocket server"""
    server = OrbitalWebSocketServer()
    
    try:
        asyncio.run(server.start_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed: {e}")

if __name__ == "__main__":
    main()