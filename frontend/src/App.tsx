import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';
import { motion } from 'framer-motion';

// Components
import Navbar from './components/Layout/Navbar';
import Dashboard from './pages/Dashboard';
import SatelliteView from './pages/SatelliteView';
import Analytics from './pages/Analytics';
import Settings from './pages/Settings';

// Context
import { SatelliteProvider } from './context/SatelliteContext';
import { WebSocketProvider } from './context/WebSocketContext';

// Theme
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#00ff9f',
      dark: '#00cc7f',
      light: '#33ffb5',
    },
    secondary: {
      main: '#0080ff',
      dark: '#0066cc',
      light: '#3399ff',
    },
    background: {
      default: '#0a0a0a',
      paper: '#1a1a1a',
    },
    text: {
      primary: '#ffffff',
      secondary: '#b0b0b0',
    },
  },
  typography: {
    fontFamily: '"Inter", "Roboto", sans-serif',
    h1: {
      fontWeight: 700,
      letterSpacing: '-0.02em',
    },
    h2: {
      fontWeight: 600,
      letterSpacing: '-0.01em',
    },
    h3: {
      fontWeight: 600,
    },
  },
  components: {
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 8,
          fontWeight: 600,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
          border: '1px solid rgba(255, 255, 255, 0.1)',
          backdropFilter: 'blur(10px)',
        },
      },
    },
  },
});

const App: React.FC = () => {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <WebSocketProvider>
        <SatelliteProvider>
          <Router>
            <div className="App">
              <Navbar />
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6 }}
                style={{ minHeight: '100vh', paddingTop: '64px' }}
              >
                <Routes>
                  <Route path="/" element={<Dashboard />} />
                  <Route path="/satellites" element={<SatelliteView />} />
                  <Route path="/analytics" element={<Analytics />} />
                  <Route path="/settings" element={<Settings />} />
                </Routes>
              </motion.div>
            </div>
          </Router>
        </SatelliteProvider>
      </WebSocketProvider>
    </ThemeProvider>
  );
};

export default App;