import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// Types
export interface Satellite {
  id: string;
  name: string;
  position: [number, number, number];
  velocity: [number, number, number];
  altitude: number;
  is_maneuvering: boolean;
  mission_type: string;
  color: string;
  norad_id: number;
}

interface SatelliteContextType {
  satellites: Satellite[];
  selectedSatellite: string | null;
  setSelectedSatellite: (id: string | null) => void;
  loading: boolean;
  error: string | null;
  refreshSatellites: () => Promise<void>;
}

// Demo data for development
const DEMO_SATELLITES: Satellite[] = [
  {
    id: '1',
    name: 'ISS (ZARYA)',
    position: [6800, 1200, 2100],
    velocity: [-1.5, 7.5, 1.2],
    altitude: 408,
    is_maneuvering: false,
    mission_type: 'space_station',
    color: '#ff0000',
    norad_id: 25544
  },
  {
    id: '2',
    name: 'HUBBLE SPACE TELESCOPE',
    position: [5800, -2100, 3400],
    velocity: [2.1, 6.8, -0.8],
    altitude: 547,
    is_maneuvering: false,
    mission_type: 'science',
    color: '#00ff00',
    norad_id: 20580
  },
  {
    id: '3',
    name: 'STARLINK-1007',
    position: [7200, 800, -1500],
    velocity: [-0.8, 7.2, 2.1],
    altitude: 550,
    is_maneuvering: true,
    mission_type: 'communication',
    color: '#0080ff',
    norad_id: 44713
  },
  {
    id: '4',
    name: 'GPS BIIA-21',
    position: [26600, 8900, 12000],
    velocity: [-2.1, 3.8, 1.2],
    altitude: 20200,
    is_maneuvering: false,
    mission_type: 'navigation',
    color: '#ffff00',
    norad_id: 26690
  },
  {
    id: '5',
    name: 'CSS (TIANHE)',
    position: [6750, -800, 2800],
    velocity: [1.2, 7.4, -0.6],
    altitude: 380,
    is_maneuvering: false,
    mission_type: 'space_station',
    color: '#ff0080',
    norad_id: 48274
  },
  {
    id: '6',
    name: 'NOAA-20',
    position: [7100, 2300, -1800],
    velocity: [-1.8, 7.1, 1.9],
    altitude: 824,
    is_maneuvering: false,
    mission_type: 'weather',
    color: '#00ff00',
    norad_id: 43013
  },
  {
    id: '7',
    name: 'STARLINK-2156',
    position: [7150, -900, 1200],
    velocity: [0.9, 7.3, -1.1],
    altitude: 540,
    is_maneuvering: false,
    mission_type: 'communication',
    color: '#0080ff',
    norad_id: 47360
  },
  {
    id: '8',
    name: 'COSMOS 2251 DEB',
    position: [8200, 1500, -2300],
    velocity: [-2.3, 6.9, 1.5],
    altitude: 790,
    is_maneuvering: false,
    mission_type: 'debris',
    color: '#808080',
    norad_id: 34454
  }
];

// Context
const SatelliteContext = createContext<SatelliteContextType | undefined>(undefined);

// Provider
interface SatelliteProviderProps {
  children: ReactNode;
}

export const SatelliteProvider: React.FC<SatelliteProviderProps> = ({ children }) => {
  const [satellites, setSatellites] = useState<Satellite[]>(DEMO_SATELLITES);
  const [selectedSatellite, setSelectedSatellite] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Simulate orbital motion
  useEffect(() => {
    const interval = setInterval(() => {
      setSatellites(prevSatellites =>
        prevSatellites.map(sat => {
          // Simple orbital motion simulation
          const radius = Math.sqrt(sat.position[0] ** 2 + sat.position[1] ** 2 + sat.position[2] ** 2);
          const orbitalSpeed = Math.sqrt(398600.4418 / radius) * 0.001; // Simplified orbital mechanics
          
          // Calculate new angle
          const currentAngle = Math.atan2(sat.position[2], sat.position[0]);
          const newAngle = currentAngle + orbitalSpeed * 0.1; // Slow down for demo
          
          // Update position
          const newX = Math.cos(newAngle) * radius;
          const newZ = Math.sin(newAngle) * radius;
          const newY = sat.position[1]; // Keep inclination simple
          
          return {
            ...sat,
            position: [newX, newY, newZ] as [number, number, number]
          };
        })
      );
    }, 1000); // Update every second

    return () => clearInterval(interval);
  }, []);

  const refreshSatellites = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // In a real implementation, this would fetch from the API
      const response = await fetch('/api/satellites');
      if (!response.ok) {
        throw new Error('Failed to fetch satellites');
      }
      
      const data = await response.json();
      setSatellites(data);
    } catch (err) {
      console.warn('API not available, using demo data');
      setError('Using demo data - API not connected');
      // Keep demo data
    } finally {
      setLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    refreshSatellites();
  }, []);

  const value: SatelliteContextType = {
    satellites,
    selectedSatellite,
    setSelectedSatellite,
    loading,
    error,
    refreshSatellites
  };

  return (
    <SatelliteContext.Provider value={value}>
      {children}
    </SatelliteContext.Provider>
  );
};

// Hook
export const useSatelliteContext = (): SatelliteContextType => {
  const context = useContext(SatelliteContext);
  if (context === undefined) {
    throw new Error('useSatelliteContext must be used within a SatelliteProvider');
  }
  return context;
};