import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  ButtonGroup,
  Switch,
  FormControlLabel,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
  LinearProgress,
} from '@mui/material';
import {
  Satellite,
  Speed,
  Visibility,
  VisibilityOff,
  Timeline,
  Warning,
  CheckCircle,
  Error,
} from '@mui/icons-material';
import { motion } from 'framer-motion';

// Components
import OrbitalScene from '../components/3D/OrbitalScene';
import { useSatelliteContext } from '../context/SatelliteContext';
import { useWebSocket } from '../context/WebSocketContext';

// Types
interface MissionAlert {
  id: string;
  type: 'warning' | 'error' | 'info' | 'success';
  message: string;
  timestamp: Date;
  satellite?: string;
}

const Dashboard: React.FC = () => {
  // Context
  const { satellites, selectedSatellite, setSelectedSatellite } = useSatelliteContext();
  const { isConnected, connectionStatus } = useWebSocket();

  // State
  const [timeSpeed, setTimeSpeed] = useState(1);
  const [showOrbits, setShowOrbits] = useState(false);
  const [showDebris, setShowDebris] = useState(true);
  const [cameraTarget, setCameraTarget] = useState<'earth' | 'satellite' | 'free'>('free');
  const [alerts, setAlerts] = useState<MissionAlert[]>([
    {
      id: '1',
      type: 'warning',
      message: 'STARLINK-1007 performing orbital maneuver',
      timestamp: new Date(),
      satellite: 'starlink1'
    },
    {
      id: '2',
      type: 'info',
      message: 'ISS approaching communication window',
      timestamp: new Date(Date.now() - 300000),
      satellite: 'iss'
    }
  ]);

  // Statistics
  const stats = {
    totalSatellites: satellites.length,
    activeSatellites: satellites.filter(s => !s.is_maneuvering).length,
    maneuveringSatellites: satellites.filter(s => s.is_maneuvering).length,
    averageAltitude: satellites.reduce((sum, s) => sum + s.altitude, 0) / satellites.length || 0,
  };

  // Mission types distribution
  const missionTypes = satellites.reduce((acc, sat) => {
    acc[sat.mission_type] = (acc[sat.mission_type] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  // Handle satellite selection
  const handleSatelliteSelect = (id: string) => {
    setSelectedSatellite(id);
    setCameraTarget('satellite');
  };

  // Time speed controls
  const timeSpeedOptions = [0, 0.5, 1, 2, 5, 10];

  return (
    <Box sx={{ minHeight: '100vh', background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%)' }}>
      <Grid container spacing={3} sx={{ p: 3 }}>
        {/* Main 3D View */}
        <Grid item xs={12} lg={8}>
          <Card sx={{ height: '600px', position: 'relative', overflow: 'hidden' }}>
            <CardContent sx={{ p: 0, height: '100%' }}>
              <OrbitalScene
                satellites={satellites}
                selectedSatellite={selectedSatellite}
                onSatelliteSelect={handleSatelliteSelect}
                showOrbits={showOrbits}
                showDebris={showDebris}
                timeSpeed={timeSpeed}
                cameraTarget={cameraTarget}
              />
            </CardContent>
          </Card>
          
          {/* Controls */}
          <Card sx={{ mt: 2 }}>
            <CardContent>
              <Grid container spacing={3} alignItems="center">
                {/* Time Controls */}
                <Grid item xs={12} sm={6} md={3}>
                  <Typography variant="subtitle2" gutterBottom>
                    Time Speed
                  </Typography>
                  <ButtonGroup variant="contained" size="small">
                    {timeSpeedOptions.map((speed) => (
                      <Button
                        key={speed}
                        onClick={() => setTimeSpeed(speed)}
                        variant={timeSpeed === speed ? 'contained' : 'outlined'}
                        sx={{ minWidth: '45px' }}
                      >
                        {speed === 0 ? '⏸' : `${speed}x`}
                      </Button>
                    ))}
                  </ButtonGroup>
                </Grid>

                {/* View Controls */}
                <Grid item xs={12} sm={6} md={3}>
                  <Typography variant="subtitle2" gutterBottom>
                    Camera Target
                  </Typography>
                  <ButtonGroup variant="outlined" size="small">
                    <Button
                      onClick={() => setCameraTarget('earth')}
                      variant={cameraTarget === 'earth' ? 'contained' : 'outlined'}
                    >
                      🌍 Earth
                    </Button>
                    <Button
                      onClick={() => setCameraTarget('satellite')}
                      variant={cameraTarget === 'satellite' ? 'contained' : 'outlined'}
                      disabled={!selectedSatellite}
                    >
                      🛰 Satellite
                    </Button>
                    <Button
                      onClick={() => setCameraTarget('free')}
                      variant={cameraTarget === 'free' ? 'contained' : 'outlined'}
                    >
                      🎮 Free
                    </Button>
                  </ButtonGroup>
                </Grid>

                {/* Display Options */}
                <Grid item xs={12} sm={12} md={6}>
                  <Typography variant="subtitle2" gutterBottom>
                    Display Options
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
                    <FormControlLabel
                      control={
                        <Switch
                          checked={showOrbits}
                          onChange={(e) => setShowOrbits(e.target.checked)}
                          color="primary"
                        />
                      }
                      label="Orbital Paths"
                    />
                    <FormControlLabel
                      control={
                        <Switch
                          checked={showDebris}
                          onChange={(e) => setShowDebris(e.target.checked)}
                          color="secondary"
                        />
                      }
                      label="Space Debris"
                    />
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} lg={4}>
          {/* Connection Status */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Typography variant="h6" sx={{ flexGrow: 1 }}>
                  System Status
                </Typography>
                <Chip
                  icon={isConnected ? <CheckCircle /> : <Error />}
                  label={isConnected ? 'Connected' : 'Disconnected'}
                  color={isConnected ? 'success' : 'error'}
                  variant="filled"
                />
              </Box>
              
              <Typography variant="body2" color="text.secondary" gutterBottom>
                {connectionStatus}
              </Typography>
              
              {!isConnected && (
                <LinearProgress color="error" sx={{ mt: 1 }} />
              )}
            </CardContent>
          </Card>

          {/* Mission Statistics */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Mission Statistics
              </Typography>
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.1 }}
                  >
                    <Box sx={{ textAlign: 'center', p: 1 }}>
                      <Typography variant="h4" color="primary">
                        {stats.totalSatellites}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Total Satellites
                      </Typography>
                    </Box>
                  </motion.div>
                </Grid>
                
                <Grid item xs={6}>
                  <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.2 }}
                  >
                    <Box sx={{ textAlign: 'center', p: 1 }}>
                      <Typography variant="h4" color="warning.main">
                        {stats.maneuveringSatellites}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Maneuvering
                      </Typography>
                    </Box>
                  </motion.div>
                </Grid>
                
                <Grid item xs={12}>
                  <motion.div
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    transition={{ delay: 0.3 }}
                  >
                    <Box sx={{ textAlign: 'center', p: 1 }}>
                      <Typography variant="h4" color="secondary">
                        {Math.round(stats.averageAltitude)}km
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Average Altitude
                      </Typography>
                    </Box>
                  </motion.div>
                </Grid>
              </Grid>

              <Divider sx={{ my: 2 }} />

              <Typography variant="subtitle2" gutterBottom>
                Mission Types
              </Typography>
              
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                {Object.entries(missionTypes).map(([type, count]) => (
                  <Chip
                    key={type}
                    label={`${type}: ${count}`}
                    variant="outlined"
                    size="small"
                  />
                ))}
              </Box>
            </CardContent>
          </Card>

          {/* Active Alerts */}
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Mission Alerts
              </Typography>
              
              <List dense>
                {alerts.map((alert) => (
                  <motion.div
                    key={alert.id}
                    initial={{ x: -20, opacity: 0 }}
                    animate={{ x: 0, opacity: 1 }}
                    transition={{ delay: 0.1 }}
                  >
                    <ListItem sx={{ px: 0 }}>
                      <ListItemIcon>
                        {alert.type === 'warning' && <Warning color="warning" />}
                        {alert.type === 'error' && <Error color="error" />}
                        {alert.type === 'info' && <Timeline color="info" />}
                        {alert.type === 'success' && <CheckCircle color="success" />}
                      </ListItemIcon>
                      <ListItemText
                        primary={alert.message}
                        secondary={alert.timestamp.toLocaleTimeString()}
                        primaryTypographyProps={{ variant: 'body2' }}
                        secondaryTypographyProps={{ variant: 'caption' }}
                      />
                    </ListItem>
                  </motion.div>
                ))}
              </List>
            </CardContent>
          </Card>

          {/* Satellite List */}
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Tracked Objects
              </Typography>
              
              <List dense sx={{ maxHeight: 300, overflow: 'auto' }}>
                {satellites.map((satellite) => (
                  <motion.div
                    key={satellite.id}
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                  >
                    <ListItem
                      button
                      selected={selectedSatellite === satellite.id}
                      onClick={() => handleSatelliteSelect(satellite.id)}
                      sx={{
                        borderRadius: 1,
                        mb: 0.5,
                        border: selectedSatellite === satellite.id ? 2 : 1,
                        borderColor: selectedSatellite === satellite.id 
                          ? 'primary.main' 
                          : 'divider',
                      }}
                    >
                      <ListItemIcon>
                        <Satellite 
                          sx={{ 
                            color: satellite.color,
                            animation: satellite.is_maneuvering ? 'pulse 1s infinite' : 'none'
                          }} 
                        />
                      </ListItemIcon>
                      <ListItemText
                        primary={
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                            {satellite.name}
                            {satellite.is_maneuvering && (
                              <Chip 
                                label="🚀" 
                                size="small" 
                                color="warning"
                                sx={{ fontSize: '10px', height: '20px' }}
                              />
                            )}
                          </Box>
                        }
                        secondary={`${Math.round(satellite.altitude)}km • ${satellite.mission_type}`}
                        primaryTypographyProps={{ variant: 'body2', fontWeight: 'medium' }}
                        secondaryTypographyProps={{ variant: 'caption' }}
                      />
                    </ListItem>
                  </motion.div>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* CSS for animations */}
      <style jsx>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
      `}</style>
    </Box>
  );
};

export default Dashboard;