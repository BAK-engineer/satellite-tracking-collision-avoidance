// 🛰️ ORBITAL NEXUS - Satellite Type Definitions

export interface TLEData {
  line1: string;
  line2: string;
  name: string;
  noradId: number;
  epoch: Date;
}

export interface OrbitalElements {
  inclination: number;
  eccentricity: number;
  raan: number; // Right Ascension of Ascending Node
  argOfPerigee: number;
  meanAnomaly: number;
  meanMotion: number;
  bstar: number;
  epochYear: number;
  epochDay: number;
}

export interface Position3D {
  x: number;
  y: number;
  z: number;
}

export interface Velocity3D {
  x: number;
  y: number;
  z: number;
}

export interface GeodeticPosition {
  latitude: number;
  longitude: number;
  altitude: number;
}

export interface SatelliteState {
  position: Position3D;
  velocity: Velocity3D;
  geodetic: GeodeticPosition;
  timestamp: Date;
}

export interface Satellite {
  id: number;
  noradId: number;
  name: string;
  type: SatelliteType;
  tle: TLEData;
  orbitalElements: OrbitalElements;
  currentState: SatelliteState;
  isActive: boolean;
  isTracked: boolean;
  lastUpdate: Date;
  nextPass?: PassPrediction;
  metadata: SatelliteMetadata;
}

export enum SatelliteType {
  COMMUNICATION = 'communication',
  NAVIGATION = 'navigation',
  WEATHER = 'weather',
  EARTH_OBSERVATION = 'earth_observation',
  SCIENTIFIC = 'scientific',
  MILITARY = 'military',
  DEBRIS = 'debris',
  AMATEUR = 'amateur',
  UNKNOWN = 'unknown'
}

export interface SatelliteMetadata {
  launchDate?: Date;
  country?: string;
  operator?: string;
  purpose?: string;
  mass?: number;
  powerSource?: string;
  status: SatelliteStatus;
  rcs?: number; // Radar Cross Section
  shape?: string;
}

export enum SatelliteStatus {
  OPERATIONAL = 'operational',
  NON_OPERATIONAL = 'non_operational',
  PARTIALLY_OPERATIONAL = 'partially_operational',
  STANDBY = 'standby',
  EXTENDED_MISSION = 'extended_mission',
  DECAYED = 'decayed',
  UNKNOWN = 'unknown'
}

export interface PassPrediction {
  startTime: Date;
  endTime: Date;
  maxElevation: number;
  maxElevationTime: Date;
  direction: string;
  brightness?: number;
}

export interface CollisionAlert {
  id: string;
  primarySatellite: Satellite;
  secondarySatellite: Satellite;
  timeToClosestApproach: Date;
  minimumDistance: number;
  probability: number;
  severity: AlertSeverity;
  recommendation: string;
  isActive: boolean;
  createdAt: Date;
}

export enum AlertSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export interface ManeuverEvent {
  id: string;
  satelliteId: number;
  timestamp: Date;
  type: ManeuverType;
  deltaV: Velocity3D;
  duration: number;
  purpose: string;
  success: boolean;
  beforeState: SatelliteState;
  afterState: SatelliteState;
}

export enum ManeuverType {
  ORBIT_RAISING = 'orbit_raising',
  ORBIT_LOWERING = 'orbit_lowering',
  INCLINATION_CHANGE = 'inclination_change',
  COLLISION_AVOIDANCE = 'collision_avoidance',
  STATION_KEEPING = 'station_keeping',
  ATTITUDE_ADJUSTMENT = 'attitude_adjustment',
  DEORBIT = 'deorbit'
}

export interface GroundStation {
  id: string;
  name: string;
  location: GeodeticPosition;
  elevation: number;
  minimumElevation: number;
  isActive: boolean;
  antennas: Antenna[];
  contacts: Contact[];
}

export interface Antenna {
  id: string;
  name: string;
  type: string;
  frequency: number;
  gain: number;
  beamwidth: number;
  azimuth: number;
  elevation: number;
}

export interface Contact {
  id: string;
  satelliteId: number;
  groundStationId: string;
  startTime: Date;
  endTime: Date;
  maxElevation: number;
  maxElevationTime: Date;
  status: ContactStatus;
  quality: number;
  dataTransferred?: number;
}

export enum ContactStatus {
  SCHEDULED = 'scheduled',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export interface OrbitPrediction {
  satellite: Satellite;
  predictions: SatelliteState[];
  timeRange: {
    start: Date;
    end: Date;
    step: number; // seconds
  };
  accuracy: number;
  model: string;
}

export interface SatelliteFilter {
  types?: SatelliteType[];
  status?: SatelliteStatus[];
  countries?: string[];
  operators?: string[];
  altitudeRange?: {
    min: number;
    max: number;
  };
  inclinationRange?: {
    min: number;
    max: number;
  };
  searchTerm?: string;
  isTracked?: boolean;
  isActive?: boolean;
}

export interface ViewSettings {
  showOrbits: boolean;
  showLabels: boolean;
  showDebris: boolean;
  showGroundTracks: boolean;
  showCommunicationLinks: boolean;
  orbitSegments: number;
  timeMultiplier: number;
  cameraMode: CameraMode;
  earthTexture: EarthTextureType;
}

export enum CameraMode {
  FREE = 'free',
  FOLLOW = 'follow',
  GROUND_TRACK = 'ground_track',
  ORBITAL = 'orbital'
}

export enum EarthTextureType {
  BLUE_MARBLE = 'blue_marble',
  NIGHT_LIGHTS = 'night_lights',
  TOPOGRAPHIC = 'topographic',
  CLOUD_COVER = 'cloud_cover'
}

export interface WebSocketMessage {
  type: MessageType;
  payload: any;
  timestamp: Date;
  sequence?: number;
}

export enum MessageType {
  SATELLITE_UPDATE = 'satellite_update',
  COLLISION_ALERT = 'collision_alert',
  MANEUVER_EVENT = 'maneuver_event',
  SYSTEM_STATUS = 'system_status',
  USER_ACTION = 'user_action',
  ERROR = 'error',
  HEARTBEAT = 'heartbeat'
}

export interface SystemStatus {
  connectedUsers: number;
  trackedSatellites: number;
  activeAlerts: number;
  systemHealth: HealthStatus;
  lastUpdate: Date;
  version: string;
  uptime: number;
}

export enum HealthStatus {
  HEALTHY = 'healthy',
  WARNING = 'warning',
  ERROR = 'error',
  CRITICAL = 'critical'
}

export interface UserPreferences {
  theme: 'dark' | 'light';
  units: 'metric' | 'imperial';
  timezone: string;
  notifications: NotificationSettings;
  display: DisplaySettings;
  shortcuts: KeyboardShortcuts;
}

export interface NotificationSettings {
  collisionAlerts: boolean;
  maneuverEvents: boolean;
  systemStatus: boolean;
  satellitePasses: boolean;
  sound: boolean;
  desktop: boolean;
}

export interface DisplaySettings {
  showFPS: boolean;
  showCoordinates: boolean;
  showVelocity: boolean;
  showTime: boolean;
  showLegend: boolean;
  renderQuality: 'low' | 'medium' | 'high' | 'ultra';
}

export interface KeyboardShortcuts {
  [key: string]: string;
}

// API Response Types
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
  timestamp: Date;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface SatelliteSearchResponse extends PaginatedResponse<Satellite> {
  filters: SatelliteFilter;
  searchTime: number;
}

// Error Types
export interface SatelliteError {
  code: string;
  message: string;
  details?: any;
  timestamp: Date;
  severity: 'info' | 'warning' | 'error' | 'critical';
}