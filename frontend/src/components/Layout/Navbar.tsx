import React, { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  IconButton,
  Menu,
  MenuItem,
  Box,
  Chip,
  Avatar,
  Divider,
  Badge,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Satellite,
  Dashboard,
  Analytics,
  Settings,
  Notifications,
  AccountCircle,
  GitHub,
  Article,
} from '@mui/icons-material';
import { useLocation, useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { useWebSocket } from '../../context/WebSocketContext';
import { useSatelliteContext } from '../../context/SatelliteContext';

const Navbar: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { isConnected } = useWebSocket();
  const { satellites } = useSatelliteContext();
  
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [userMenuAnchor, setUserMenuAnchor] = useState<null | HTMLElement>(null);
  
  const activeSatellites = satellites.filter(s => !s.is_maneuvering).length;
  const maneuveringSatellites = satellites.filter(s => s.is_maneuvering).length;

  const navigation = [
    { name: 'Dashboard', path: '/', icon: <Dashboard /> },
    { name: 'Satellites', path: '/satellites', icon: <Satellite /> },
    { name: 'Analytics', path: '/analytics', icon: <Analytics /> },
    { name: 'Settings', path: '/settings', icon: <Settings /> },
  ];

  const handleNavigation = (path: string) => {
    navigate(path);
    setAnchorEl(null);
  };

  const handleUserMenu = (event: React.MouseEvent<HTMLElement>) => {
    setUserMenuAnchor(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setUserMenuAnchor(null);
  };

  return (
    <AppBar 
      position="fixed" 
      sx={{ 
        backgroundColor: 'rgba(10, 10, 10, 0.95)',
        backdropFilter: 'blur(10px)',
        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
      }}
    >
      <Toolbar>
        {/* Logo and Title */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.5 }}
          style={{ display: 'flex', alignItems: 'center', marginRight: '2rem' }}
        >
          <Satellite sx={{ mr: 1, fontSize: 28, color: 'primary.main' }} />
          <Typography 
            variant="h6" 
            component="div" 
            sx={{ 
              fontWeight: 700,
              background: 'linear-gradient(45deg, #00ff9f 30%, #0080ff 90%)',
              backgroundClip: 'text',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}
          >
            ORBITAL NEXUS
          </Typography>
        </motion.div>

        {/* Navigation Links - Desktop */}
        <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex' }, gap: 1 }}>
          {navigation.map((item) => (
            <motion.div
              key={item.path}
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <Button
                color="inherit"
                startIcon={item.icon}
                onClick={() => handleNavigation(item.path)}
                sx={{
                  borderRadius: 2,
                  px: 2,
                  py: 1,
                  backgroundColor: location.pathname === item.path ? 'rgba(0, 255, 159, 0.1)' : 'transparent',
                  border: location.pathname === item.path ? '1px solid rgba(0, 255, 159, 0.3)' : '1px solid transparent',
                  color: location.pathname === item.path ? 'primary.main' : 'inherit',
                  '&:hover': {
                    backgroundColor: 'rgba(0, 255, 159, 0.05)',
                    border: '1px solid rgba(0, 255, 159, 0.2)',
                  },
                }}
              >
                {item.name}
              </Button>
            </motion.div>
          ))}
        </Box>

        {/* Status Indicators */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          {/* Connection Status */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.3 }}
          >
            <Chip
              icon={
                <Box
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: '50%',
                    backgroundColor: isConnected ? 'success.main' : 'error.main',
                    animation: isConnected ? 'pulse 2s infinite' : 'none',
                  }}
                />
              }
              label={isConnected ? 'Live' : 'Offline'}
              variant="outlined"
              size="small"
              sx={{
                borderColor: isConnected ? 'success.main' : 'error.main',
                color: isConnected ? 'success.main' : 'error.main',
                '& .MuiChip-icon': {
                  color: 'inherit',
                },
              }}
            />
          </motion.div>

          {/* Satellite Count */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.4 }}
          >
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Chip
                label={`${activeSatellites} Active`}
                size="small"
                color="primary"
                variant="outlined"
              />
              {maneuveringSatellites > 0 && (
                <Chip
                  label={`${maneuveringSatellites} Maneuvering`}
                  size="small"
                  color="warning"
                  variant="filled"
                  sx={{ animation: 'pulse 1.5s infinite' }}
                />
              )}
            </Box>
          </motion.div>

          {/* Notifications */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
          >
            <IconButton color="inherit" sx={{ '&:hover': { color: 'primary.main' } }}>
              <Badge badgeContent={maneuveringSatellites} color="warning">
                <Notifications />
              </Badge>
            </IconButton>
          </motion.div>

          {/* User Menu */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6 }}
          >
            <IconButton
              size="large"
              aria-label="account of current user"
              aria-controls="user-menu"
              aria-haspopup="true"
              onClick={handleUserMenu}
              color="inherit"
              sx={{ '&:hover': { color: 'primary.main' } }}
            >
              <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
                <AccountCircle />
              </Avatar>
            </IconButton>
          </motion.div>

          {/* Mobile Menu */}
          <Box sx={{ display: { xs: 'flex', md: 'none' } }}>
            <IconButton
              size="large"
              aria-label="menu"
              aria-controls="mobile-menu"
              aria-haspopup="true"
              onClick={(e) => setAnchorEl(e.currentTarget)}
              color="inherit"
            >
              <MenuIcon />
            </IconButton>
          </Box>
        </Box>

        {/* Mobile Menu */}
        <Menu
          id="mobile-menu"
          anchorEl={anchorEl}
          anchorOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
          keepMounted
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
          open={Boolean(anchorEl)}
          onClose={() => setAnchorEl(null)}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiPaper-root': {
              backgroundColor: 'rgba(26, 26, 26, 0.95)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
            },
          }}
        >
          {navigation.map((item) => (
            <MenuItem 
              key={item.path}
              onClick={() => handleNavigation(item.path)}
              selected={location.pathname === item.path}
              sx={{
                '&.Mui-selected': {
                  backgroundColor: 'rgba(0, 255, 159, 0.1)',
                  color: 'primary.main',
                },
              }}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {item.icon}
                {item.name}
              </Box>
            </MenuItem>
          ))}
        </Menu>

        {/* User Menu */}
        <Menu
          id="user-menu"
          anchorEl={userMenuAnchor}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          keepMounted
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
          open={Boolean(userMenuAnchor)}
          onClose={handleUserMenuClose}
          sx={{
            '& .MuiPaper-root': {
              backgroundColor: 'rgba(26, 26, 26, 0.95)',
              backdropFilter: 'blur(10px)',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              minWidth: 200,
            },
          }}
        >
          <Box sx={{ px: 2, py: 1 }}>
            <Typography variant="subtitle2" color="text.secondary">
              Orbital Nexus User
            </Typography>
            <Typography variant="body2" color="primary">
              mission.control@orbitalnexus.dev
            </Typography>
          </Box>
          <Divider />
          <MenuItem onClick={handleUserMenuClose}>
            <AccountCircle sx={{ mr: 1 }} />
            Profile
          </MenuItem>
          <MenuItem onClick={handleUserMenuClose}>
            <Settings sx={{ mr: 1 }} />
            Settings
          </MenuItem>
          <MenuItem onClick={handleUserMenuClose}>
            <Article sx={{ mr: 1 }} />
            Documentation
          </MenuItem>
          <MenuItem 
            onClick={() => window.open('https://github.com/orbital-nexus/platform', '_blank')}
          >
            <GitHub sx={{ mr: 1 }} />
            GitHub
          </MenuItem>
          <Divider />
          <MenuItem onClick={handleUserMenuClose} sx={{ color: 'error.main' }}>
            Logout
          </MenuItem>
        </Menu>
      </Toolbar>

      {/* CSS for animations */}
      <style jsx>{`
        @keyframes pulse {
          0% { opacity: 1; }
          50% { opacity: 0.5; }
          100% { opacity: 1; }
        }
      `}</style>
    </AppBar>
  );
};

export default Navbar;