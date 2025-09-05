import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import { io, Socket } from 'socket.io-client';

// Types
interface WebSocketContextType {
  socket: Socket | null;
  isConnected: boolean;
  connectionStatus: string;
  lastMessage: any;
  sendMessage: (message: any) => void;
}

// Context
const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

// Provider
interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('Disconnected');
  const [lastMessage, setLastMessage] = useState<any>(null);

  useEffect(() => {
    // Get WebSocket URL from environment or use default
    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';
    
    // Create WebSocket connection
    const newSocket = io(wsUrl, {
      transports: ['websocket', 'polling'],
      upgrade: true,
      rememberUpgrade: true,
      timeout: 20000,
      forceNew: true
    });

    // Connection event handlers
    newSocket.on('connect', () => {
      console.log('🔗 WebSocket connected');
      setIsConnected(true);
      setConnectionStatus('Connected to Orbital Nexus');
    });

    newSocket.on('disconnect', (reason) => {
      console.log('❌ WebSocket disconnected:', reason);
      setIsConnected(false);
      setConnectionStatus(`Disconnected: ${reason}`);
    });

    newSocket.on('connect_error', (error) => {
      console.error('🔥 WebSocket connection error:', error);
      setIsConnected(false);
      setConnectionStatus(`Connection error: ${error.message}`);
    });

    newSocket.on('reconnect', (attemptNumber) => {
      console.log('🔄 WebSocket reconnected after', attemptNumber, 'attempts');
      setIsConnected(true);
      setConnectionStatus('Reconnected to Orbital Nexus');
    });

    newSocket.on('reconnect_attempt', (attemptNumber) => {
      console.log('🔄 WebSocket reconnection attempt:', attemptNumber);
      setConnectionStatus(`Reconnecting... (attempt ${attemptNumber})`);
    });

    newSocket.on('reconnect_error', (error) => {
      console.error('🔥 WebSocket reconnection error:', error);
      setConnectionStatus(`Reconnection failed: ${error.message}`);
    });

    newSocket.on('reconnect_failed', () => {
      console.error('💀 WebSocket reconnection failed');
      setConnectionStatus('Reconnection failed - using offline mode');
    });

    // Data event handlers
    newSocket.on('satellite_update', (data) => {
      console.log('📡 Received satellite update:', data);
      setLastMessage({
        type: 'satellite_update',
        data: data,
        timestamp: new Date().toISOString()
      });
    });

    newSocket.on('system_alert', (data) => {
      console.log('⚠️ Received system alert:', data);
      setLastMessage({
        type: 'system_alert',
        data: data,
        timestamp: new Date().toISOString()
      });
    });

    newSocket.on('collision_warning', (data) => {
      console.log('🚨 Received collision warning:', data);
      setLastMessage({
        type: 'collision_warning',
        data: data,
        timestamp: new Date().toISOString()
      });
    });

    // Custom message handler
    newSocket.on('message', (data) => {
      console.log('📨 Received message:', data);
      setLastMessage({
        type: 'message',
        data: data,
        timestamp: new Date().toISOString()
      });
    });

    setSocket(newSocket);

    // Cleanup on unmount
    return () => {
      console.log('🧹 Cleaning up WebSocket connection');
      newSocket.close();
    };
  }, []);

  // Send message function
  const sendMessage = (message: any) => {
    if (socket && isConnected) {
      socket.emit('message', message);
      console.log('📤 Sent message:', message);
    } else {
      console.warn('⚠️ Cannot send message - WebSocket not connected');
    }
  };

  // Heartbeat to keep connection alive
  useEffect(() => {
    if (!socket || !isConnected) return;

    const heartbeat = setInterval(() => {
      sendMessage({ type: 'ping', timestamp: new Date().toISOString() });
    }, 30000); // Send ping every 30 seconds

    return () => clearInterval(heartbeat);
  }, [socket, isConnected]);

  // Handle page visibility changes
  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.hidden) {
        console.log('📱 Page hidden - reducing WebSocket activity');
      } else {
        console.log('📱 Page visible - resuming normal WebSocket activity');
        if (socket && !isConnected) {
          socket.connect();
        }
      }
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, [socket, isConnected]);

  // Fallback for when WebSocket is not available
  useEffect(() => {
    if (!isConnected) {
      // Use polling as fallback (demo mode)
      const fallbackInterval = setInterval(() => {
        setLastMessage({
          type: 'demo_update',
          data: {
            message: 'Demo mode - WebSocket not available',
            satellites_count: 8,
            maneuvering_count: 1
          },
          timestamp: new Date().toISOString()
        });
      }, 5000);

      return () => clearInterval(fallbackInterval);
    }
  }, [isConnected]);

  const value: WebSocketContextType = {
    socket,
    isConnected,
    connectionStatus,
    lastMessage,
    sendMessage
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

// Hook
export const useWebSocket = (): WebSocketContextType => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};