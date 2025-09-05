// 🛰️ ORBITAL NEXUS - API Service Layer

import { 
  Satellite, 
  SatelliteFilter, 
  SatelliteSearchResponse, 
  CollisionAlert, 
  ManeuverEvent, 
  SystemStatus,
  ApiResponse,
  PaginatedResponse,
  GroundStation,
  OrbitPrediction
} from '../types/satellite';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';
const WS_BASE_URL = process.env.REACT_APP_WS_URL || 'ws://localhost:8000';

class ApiService {
  private baseURL: string;
  private wsURL: string;
  
  constructor() {
    this.baseURL = API_BASE_URL;
    this.wsURL = WS_BASE_URL;
  }

  /**
   * Generic API request handler with error handling
   */
  private async request<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<ApiResponse<T>> {
    try {
      const response = await fetch(`${this.baseURL}${endpoint}`, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return {
        success: true,
        data,
        timestamp: new Date(),
      };
    } catch (error) {
      console.error(`API Error for ${endpoint}:`, error);
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Unknown error',
        timestamp: new Date(),
      };
    }
  }

  // ========================================
  // SATELLITE ENDPOINTS
  // ========================================

  /**
   * Get all satellites with optional filtering and pagination
   */
  async getSatellites(
    filter?: SatelliteFilter,
    page: number = 1,
    pageSize: number = 50
  ): Promise<SatelliteSearchResponse | null> {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });

    if (filter) {
      if (filter.types) params.append('types', filter.types.join(','));
      if (filter.status) params.append('status', filter.status.join(','));
      if (filter.countries) params.append('countries', filter.countries.join(','));
      if (filter.searchTerm) params.append('search', filter.searchTerm);
      if (filter.isTracked !== undefined) params.append('tracked', filter.isTracked.toString());
      if (filter.isActive !== undefined) params.append('active', filter.isActive.toString());
      if (filter.altitudeRange) {
        params.append('min_altitude', filter.altitudeRange.min.toString());
        params.append('max_altitude', filter.altitudeRange.max.toString());
      }
    }

    const response = await this.request<SatelliteSearchResponse>(
      `/api/v1/satellites?${params.toString()}`
    );

    return response.success ? response.data! : null;
  }

  /**
   * Get satellite by ID
   */
  async getSatellite(id: number): Promise<Satellite | null> {
    const response = await this.request<Satellite>(`/api/v1/satellites/${id}`);
    return response.success ? response.data! : null;
  }

  /**
   * Get satellite by NORAD ID
   */
  async getSatelliteByNoradId(noradId: number): Promise<Satellite | null> {
    const response = await this.request<Satellite>(`/api/v1/satellites/norad/${noradId}`);
    return response.success ? response.data! : null;
  }

  /**
   * Update satellite tracking status
   */
  async updateSatelliteTracking(id: number, tracked: boolean): Promise<boolean> {
    const response = await this.request<{ success: boolean }>(
      `/api/v1/satellites/${id}/tracking`,
      {
        method: 'PATCH',
        body: JSON.stringify({ tracked }),
      }
    );
    return response.success && response.data?.success === true;
  }

  /**
   * Get satellite orbital predictions
   */
  async getSatellitePredictions(
    id: number,
    startTime: Date,
    endTime: Date,
    stepSize: number = 60
  ): Promise<OrbitPrediction | null> {
    const params = new URLSearchParams({
      start_time: startTime.toISOString(),
      end_time: endTime.toISOString(),
      step_size: stepSize.toString(),
    });

    const response = await this.request<OrbitPrediction>(
      `/api/v1/satellites/${id}/predictions?${params.toString()}`
    );

    return response.success ? response.data! : null;
  }

  // ========================================
  // COLLISION DETECTION ENDPOINTS
  // ========================================

  /**
   * Get active collision alerts
   */
  async getCollisionAlerts(): Promise<CollisionAlert[]> {
    const response = await this.request<CollisionAlert[]>('/api/v1/collisions/alerts');
    return response.success ? response.data! : [];
  }

  /**
   * Get collision alert by ID
   */
  async getCollisionAlert(id: string): Promise<CollisionAlert | null> {
    const response = await this.request<CollisionAlert>(`/api/v1/collisions/alerts/${id}`);
    return response.success ? response.data! : null;
  }

  /**
   * Acknowledge collision alert
   */
  async acknowledgeAlert(id: string): Promise<boolean> {
    const response = await this.request<{ success: boolean }>(
      `/api/v1/collisions/alerts/${id}/acknowledge`,
      { method: 'POST' }
    );
    return response.success && response.data?.success === true;
  }

  // ========================================
  // MANEUVER ENDPOINTS
  // ========================================

  /**
   * Get maneuver events for a satellite
   */
  async getManeuverEvents(satelliteId?: number): Promise<ManeuverEvent[]> {
    const endpoint = satelliteId 
      ? `/api/v1/maneuvers?satellite_id=${satelliteId}`
      : '/api/v1/maneuvers';
    
    const response = await this.request<ManeuverEvent[]>(endpoint);
    return response.success ? response.data! : [];
  }

  /**
   * Get recent maneuver events
   */
  async getRecentManeuvers(limit: number = 10): Promise<ManeuverEvent[]> {
    const response = await this.request<ManeuverEvent[]>(
      `/api/v1/maneuvers/recent?limit=${limit}`
    );
    return response.success ? response.data! : [];
  }

  // ========================================
  // GROUND STATION ENDPOINTS
  // ========================================

  /**
   * Get all ground stations
   */
  async getGroundStations(): Promise<GroundStation[]> {
    const response = await this.request<GroundStation[]>('/api/v1/ground-stations');
    return response.success ? response.data! : [];
  }

  /**
   * Get ground station by ID
   */
  async getGroundStation(id: string): Promise<GroundStation | null> {
    const response = await this.request<GroundStation>(`/api/v1/ground-stations/${id}`);
    return response.success ? response.data! : null;
  }

  // ========================================
  // TLE DATA ENDPOINTS
  // ========================================

  /**
   * Update TLE data for all satellites
   */
  async updateTleData(): Promise<boolean> {
    const response = await this.request<{ success: boolean }>(
      '/api/v1/tle/update',
      { method: 'POST' }
    );
    return response.success && response.data?.success === true;
  }

  /**
   * Get TLE data update status
   */
  async getTleUpdateStatus(): Promise<{ lastUpdate: Date; nextUpdate: Date; status: string } | null> {
    const response = await this.request<{ lastUpdate: string; nextUpdate: string; status: string }>(
      '/api/v1/tle/status'
    );
    
    if (response.success && response.data) {
      return {
        lastUpdate: new Date(response.data.lastUpdate),
        nextUpdate: new Date(response.data.nextUpdate),
        status: response.data.status
      };
    }
    return null;
  }

  // ========================================
  // SYSTEM STATUS ENDPOINTS
  // ========================================

  /**
   * Get system status
   */
  async getSystemStatus(): Promise<SystemStatus | null> {
    const response = await this.request<SystemStatus>('/api/v1/system/status');
    return response.success ? response.data! : null;
  }

  /**
   * Get system health check
   */
  async getHealthCheck(): Promise<{ status: string; checks: Record<string, boolean> } | null> {
    const response = await this.request<{ status: string; checks: Record<string, boolean> }>(
      '/api/v1/system/health'
    );
    return response.success ? response.data! : null;
  }

  /**
   * Get system metrics
   */
  async getSystemMetrics(): Promise<Record<string, any> | null> {
    const response = await this.request<Record<string, any>>('/api/v1/system/metrics');
    return response.success ? response.data! : null;
  }

  // ========================================
  // SEARCH AND DISCOVERY
  // ========================================

  /**
   * Search satellites by name or NORAD ID
   */
  async searchSatellites(query: string): Promise<Satellite[]> {
    const response = await this.request<Satellite[]>(
      `/api/v1/search?q=${encodeURIComponent(query)}`
    );
    return response.success ? response.data! : [];
  }

  /**
   * Get popular satellites
   */
  async getPopularSatellites(): Promise<Satellite[]> {
    const response = await this.request<Satellite[]>('/api/v1/satellites/popular');
    return response.success ? response.data! : [];
  }

  /**
   * Get satellites by type
   */
  async getSatellitesByType(type: string): Promise<Satellite[]> {
    const response = await this.request<Satellite[]>(`/api/v1/satellites/type/${type}`);
    return response.success ? response.data! : [];
  }

  // ========================================
  // ANALYTICS ENDPOINTS
  // ========================================

  /**
   * Get satellite statistics
   */
  async getSatelliteStats(): Promise<Record<string, number> | null> {
    const response = await this.request<Record<string, number>>('/api/v1/analytics/stats');
    return response.success ? response.data! : null;
  }

  /**
   * Get orbital distribution data
   */
  async getOrbitalDistribution(): Promise<any[] | null> {
    const response = await this.request<any[]>('/api/v1/analytics/orbital-distribution');
    return response.success ? response.data! : null;
  }

  // ========================================
  // WEBSOCKET CONNECTION
  // ========================================

  /**
   * Create WebSocket connection for real-time updates
   */
  createWebSocketConnection(): WebSocket {
    const ws = new WebSocket(`${this.wsURL}/ws`);
    
    ws.onopen = () => {
      console.log('🛰️ WebSocket connected to Orbital Nexus');
    };

    ws.onclose = (event) => {
      console.log('🛰️ WebSocket disconnected:', event.code, event.reason);
    };

    ws.onerror = (error) => {
      console.error('🛰️ WebSocket error:', error);
    };

    return ws;
  }

  // ========================================
  // UTILITY METHODS
  // ========================================

  /**
   * Check if API is available
   */
  async isApiAvailable(): Promise<boolean> {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/health`);
      return response.ok;
    } catch {
      return false;
    }
  }

  /**
   * Get API version
   */
  async getApiVersion(): Promise<string | null> {
    const response = await this.request<{ version: string }>('/api/v1/version');
    return response.success ? response.data?.version || null : null;
  }

  /**
   * Upload TLE file
   */
  async uploadTleFile(file: File): Promise<boolean> {
    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await fetch(`${this.baseURL}/api/v1/tle/upload`, {
        method: 'POST',
        body: formData,
      });

      return response.ok;
    } catch (error) {
      console.error('TLE upload error:', error);
      return false;
    }
  }

  /**
   * Export satellites data
   */
  async exportSatellites(format: 'json' | 'csv' | 'tle' = 'json'): Promise<Blob | null> {
    try {
      const response = await fetch(`${this.baseURL}/api/v1/satellites/export?format=${format}`);
      if (response.ok) {
        return await response.blob();
      }
    } catch (error) {
      console.error('Export error:', error);
    }
    return null;
  }
}

// Create and export singleton instance
export const apiService = new ApiService();
export default apiService;