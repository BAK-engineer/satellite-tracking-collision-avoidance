import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  TextField,
  InputAdornment,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  LinearProgress,
} from '@mui/material';
import {
  Search,
  Satellite,
  Visibility,
  Launch,
  Speed,
  Height,
  Navigation,
  Science,
  Communication,
  Warning,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useSatelliteContext } from '../context/SatelliteContext';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`satellite-tabpanel-${index}`}
      aria-labelledby={`satellite-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const SatelliteView: React.FC = () => {
  const { satellites, setSelectedSatellite } = useSatelliteContext();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedType, setSelectedType] = useState('all');
  const [detailsOpen, setDetailsOpen] = useState(false);
  const [selectedSat, setSelectedSat] = useState<any>(null);
  const [tabValue, setTabValue] = useState(0);

  // Filter satellites
  const filteredSatellites = satellites.filter(sat => {
    const matchesSearch = sat.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         sat.norad_id.toString().includes(searchTerm);
    const matchesType = selectedType === 'all' || sat.mission_type === selectedType;
    return matchesSearch && matchesType;
  });

  // Mission type icons
  const getMissionIcon = (type: string) => {
    switch (type) {
      case 'space_station': return <Launch color="error" />;
      case 'communication': return <Communication color="primary" />;
      case 'navigation': return <Navigation color="warning" />;
      case 'science': return <Science color="secondary" />;
      case 'weather': return <Height color="info" />;
      case 'debris': return <Warning color="disabled" />;
      default: return <Satellite color="action" />;
    }
  };

  // Get status color
  const getStatusColor = (satellite: any) => {
    if (satellite.is_maneuvering) return 'warning';
    if (satellite.mission_type === 'debris') return 'error';
    return 'success';
  };

  const handleSatelliteClick = (satellite: any) => {
    setSelectedSat(satellite);
    setDetailsOpen(true);
    setSelectedSatellite(satellite.id);
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Box sx={{ minHeight: '100vh', background: 'linear-gradient(135deg, #0a0a0a 0%, #1a1a2e 100%)', p: 3 }}>
      {/* Header */}
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <Typography variant="h4" gutterBottom sx={{ color: 'primary.main', fontWeight: 700 }}>
          🛰️ Satellite Tracking Center
        </Typography>
        <Typography variant="subtitle1" color="text.secondary" sx={{ mb: 3 }}>
          Real-time monitoring of {satellites.length} orbital objects
        </Typography>
      </motion.div>

      {/* Filters */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.2 }}
      >
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Grid container spacing={2} alignItems="center">
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  placeholder="Search satellites by name or NORAD ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  InputProps={{
                    startAdornment: (
                      <InputAdornment position="start">
                        <Search color="action" />
                      </InputAdornment>
                    ),
                  }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  {['all', 'space_station', 'communication', 'navigation', 'science', 'weather', 'debris'].map((type) => (
                    <Chip
                      key={type}
                      label={type.replace('_', ' ').toUpperCase()}
                      variant={selectedType === type ? 'filled' : 'outlined'}
                      color={selectedType === type ? 'primary' : 'default'}
                      onClick={() => setSelectedType(type)}
                      size="small"
                    />
                  ))}
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </motion.div>

      {/* Statistics Cards */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
      >
        <Grid container spacing={3} sx={{ mb: 3 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="primary">
                  {satellites.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Total Satellites
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main">
                  {satellites.filter(s => s.is_maneuvering).length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Maneuvering
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">
                  {satellites.filter(s => !s.is_maneuvering && s.mission_type !== 'debris').length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Operational
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="error.main">
                  {satellites.filter(s => s.mission_type === 'debris').length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Debris Objects
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </motion.div>

      {/* Satellites Table */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.6 }}
      >
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Satellite Catalog ({filteredSatellites.length} objects)
            </Typography>
            
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Object</TableCell>
                    <TableCell>NORAD ID</TableCell>
                    <TableCell>Mission Type</TableCell>
                    <TableCell>Altitude (km)</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredSatellites.map((satellite) => (
                    <motion.tr
                      key={satellite.id}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      transition={{ delay: 0.1 }}
                      component="tr"
                      whileHover={{ backgroundColor: 'rgba(0, 255, 159, 0.05)' }}
                    >
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          {getMissionIcon(satellite.mission_type)}
                          <Box>
                            <Typography variant="body2" fontWeight="medium">
                              {satellite.name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {satellite.mission_type.replace('_', ' ').toUpperCase()}
                            </Typography>
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" fontFamily="monospace">
                          {satellite.norad_id}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={satellite.mission_type.replace('_', ' ')}
                          size="small"
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {Math.round(satellite.altitude).toLocaleString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={satellite.is_maneuvering ? 'Maneuvering' : 'Nominal'}
                          color={getStatusColor(satellite)}
                          size="small"
                          icon={satellite.is_maneuvering ? <Speed /> : undefined}
                        />
                      </TableCell>
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={() => handleSatelliteClick(satellite)}
                          color="primary"
                        >
                          <Visibility />
                        </IconButton>
                      </TableCell>
                    </motion.tr>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </motion.div>

      {/* Satellite Details Dialog */}
      <Dialog
        open={detailsOpen}
        onClose={() => setDetailsOpen(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedSat && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {getMissionIcon(selectedSat.mission_type)}
                {selectedSat.name}
                {selectedSat.is_maneuvering && (
                  <Chip label="Maneuvering" color="warning" size="small" />
                )}
              </Box>
            </DialogTitle>
            <DialogContent>
              <Tabs value={tabValue} onChange={handleTabChange}>
                <Tab label="Overview" />
                <Tab label="Orbital Data" />
                <Tab label="Telemetry" />
              </Tabs>

              {/* Overview Tab */}
              <TabPanel value={tabValue} index={0}>
                <Grid container spacing={3}>
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" gutterBottom>Basic Information</Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">NORAD ID:</Typography>
                        <Typography variant="body2" fontFamily="monospace">{selectedSat.norad_id}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Mission Type:</Typography>
                        <Typography variant="body2">{selectedSat.mission_type.replace('_', ' ')}</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Status:</Typography>
                        <Chip
                          label={selectedSat.is_maneuvering ? 'Maneuvering' : 'Nominal'}
                          color={getStatusColor(selectedSat)}
                          size="small"
                        />
                      </Box>
                    </Box>
                  </Grid>
                  <Grid item xs={12} md={6}>
                    <Typography variant="h6" gutterBottom>Current State</Typography>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Altitude:</Typography>
                        <Typography variant="body2">{Math.round(selectedSat.altitude).toLocaleString()} km</Typography>
                      </Box>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                        <Typography variant="body2" color="text.secondary">Velocity:</Typography>
                        <Typography variant="body2">
                          {Math.sqrt(selectedSat.velocity[0]**2 + selectedSat.velocity[1]**2 + selectedSat.velocity[2]**2).toFixed(2)} km/s
                        </Typography>
                      </Box>
                    </Box>
                  </Grid>
                </Grid>
              </TabPanel>

              {/* Orbital Data Tab */}
              <TabPanel value={tabValue} index={1}>
                <Typography variant="h6" gutterBottom>Orbital Elements</Typography>
                <Grid container spacing={2}>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">Position (ECI):</Typography>
                    <Typography variant="body2" fontFamily="monospace">
                      [{selectedSat.position.map((p: number) => p.toFixed(1)).join(', ')}] km
                    </Typography>
                  </Grid>
                  <Grid item xs={6}>
                    <Typography variant="body2" color="text.secondary">Velocity (ECI):</Typography>
                    <Typography variant="body2" fontFamily="monospace">
                      [{selectedSat.velocity.map((v: number) => v.toFixed(3)).join(', ')}] km/s
                    </Typography>
                  </Grid>
                </Grid>
              </TabPanel>

              {/* Telemetry Tab */}
              <TabPanel value={tabValue} index={2}>
                <Typography variant="h6" gutterBottom>Real-time Telemetry</Typography>
                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                  Live data stream from satellite tracking network
                </Typography>
                <LinearProgress sx={{ mb: 2 }} />
                <Typography variant="body2">
                  Telemetry data would be displayed here in a real implementation.
                </Typography>
              </TabPanel>
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setDetailsOpen(false)}>Close</Button>
              <Button variant="contained" onClick={() => setSelectedSatellite(selectedSat.id)}>
                Track in 3D View
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};

export default SatelliteView;