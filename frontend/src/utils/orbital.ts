// 🛰️ ORBITAL NEXUS - Orbital Mechanics Utilities

import { Position3D, Velocity3D, GeodeticPosition, SatelliteState, OrbitalElements } from '../types/satellite';

// Constants
export const EARTH_RADIUS_KM = 6378.137;
export const EARTH_FLATTENING = 1 / 298.257223563;
export const GRAVITATIONAL_PARAMETER = 398600.4418; // km³/s²
export const EARTH_ROTATION_RATE = 7.2921159e-5; // rad/s
export const J2_COEFFICIENT = 1.08262668e-3;
export const SPEED_OF_LIGHT = 299792458; // m/s

/**
 * Convert ECI (Earth Centered Inertial) coordinates to geodetic coordinates
 */
export function eciToGeodetic(position: Position3D, gmst: number): GeodeticPosition {
  const { x, y, z } = position;
  
  // Convert to Earth-fixed coordinates
  const xEarth = x * Math.cos(gmst) + y * Math.sin(gmst);
  const yEarth = -x * Math.sin(gmst) + y * Math.cos(gmst);
  const zEarth = z;
  
  // Calculate longitude
  let longitude = Math.atan2(yEarth, xEarth) * 180 / Math.PI;
  if (longitude < -180) longitude += 360;
  if (longitude > 180) longitude -= 360;
  
  // Calculate latitude and altitude using iterative method
  const r = Math.sqrt(xEarth * xEarth + yEarth * yEarth);
  let latitude = Math.atan2(zEarth, r);
  let altitude = 0;
  
  // Iterative calculation for accurate geodetic coordinates
  for (let i = 0; i < 10; i++) {
    const sinLat = Math.sin(latitude);
    const cosLat = Math.cos(latitude);
    const e2 = 2 * EARTH_FLATTENING - EARTH_FLATTENING * EARTH_FLATTENING;
    const N = EARTH_RADIUS_KM / Math.sqrt(1 - e2 * sinLat * sinLat);
    
    altitude = r / cosLat - N;
    const newLatitude = Math.atan2(zEarth, r * (1 - e2 * N / (N + altitude)));
    
    if (Math.abs(newLatitude - latitude) < 1e-10) break;
    latitude = newLatitude;
  }
  
  return {
    latitude: latitude * 180 / Math.PI,
    longitude,
    altitude
  };
}

/**
 * Convert geodetic coordinates to ECI coordinates
 */
export function geodeticToEci(geodetic: GeodeticPosition, gmst: number): Position3D {
  const { latitude, longitude, altitude } = geodetic;
  
  const latRad = latitude * Math.PI / 180;
  const lonRad = longitude * Math.PI / 180;
  
  const sinLat = Math.sin(latRad);
  const cosLat = Math.cos(latRad);
  const sinLon = Math.sin(lonRad);
  const cosLon = Math.cos(lonRad);
  
  const e2 = 2 * EARTH_FLATTENING - EARTH_FLATTENING * EARTH_FLATTENING;
  const N = EARTH_RADIUS_KM / Math.sqrt(1 - e2 * sinLat * sinLat);
  
  // Earth-fixed coordinates
  const xEarth = (N + altitude) * cosLat * cosLon;
  const yEarth = (N + altitude) * cosLat * sinLon;
  const zEarth = (N * (1 - e2) + altitude) * sinLat;
  
  // Convert to ECI coordinates
  const x = xEarth * Math.cos(gmst) - yEarth * Math.sin(gmst);
  const y = xEarth * Math.sin(gmst) + yEarth * Math.cos(gmst);
  const z = zEarth;
  
  return { x, y, z };
}

/**
 * Calculate Greenwich Mean Sidereal Time
 */
export function calculateGMST(date: Date): number {
  const JD2000 = 2451545.0; // Julian Date for J2000.0 epoch
  const julianDate = (date.getTime() / 86400000) + 2440587.5;
  const t = (julianDate - JD2000) / 36525.0;
  
  // GMST at 0h UT
  let gmst = 280.46061837 + 360.98564736629 * (julianDate - JD2000) + 
             0.000387933 * t * t - t * t * t / 38710000.0;
  
  // Add the time of day
  const hours = date.getUTCHours();
  const minutes = date.getUTCMinutes();
  const seconds = date.getUTCSeconds();
  const timeOfDay = (hours + minutes / 60 + seconds / 3600) * 15; // degrees
  
  gmst = (gmst + timeOfDay) % 360;
  if (gmst < 0) gmst += 360;
  
  return gmst * Math.PI / 180; // Convert to radians
}

/**
 * Calculate distance between two positions
 */
export function calculateDistance(pos1: Position3D, pos2: Position3D): number {
  const dx = pos2.x - pos1.x;
  const dy = pos2.y - pos1.y;
  const dz = pos2.z - pos1.z;
  return Math.sqrt(dx * dx + dy * dy + dz * dz);
}

/**
 * Calculate relative velocity between two objects
 */
export function calculateRelativeVelocity(vel1: Velocity3D, vel2: Velocity3D): Velocity3D {
  return {
    x: vel1.x - vel2.x,
    y: vel1.y - vel2.y,
    z: vel1.z - vel2.z
  };
}

/**
 * Calculate orbital period from semi-major axis
 */
export function calculateOrbitalPeriod(semiMajorAxis: number): number {
  return 2 * Math.PI * Math.sqrt(Math.pow(semiMajorAxis, 3) / GRAVITATIONAL_PARAMETER);
}

/**
 * Calculate semi-major axis from mean motion
 */
export function calculateSemiMajorAxis(meanMotion: number): number {
  const n = meanMotion * 2 * Math.PI / 86400; // Convert rev/day to rad/s
  return Math.pow(GRAVITATIONAL_PARAMETER / (n * n), 1/3);
}

/**
 * Calculate apogee and perigee from orbital elements
 */
export function calculateApogeePerigee(elements: OrbitalElements): { apogee: number; perigee: number } {
  const semiMajorAxis = calculateSemiMajorAxis(elements.meanMotion);
  const apogee = semiMajorAxis * (1 + elements.eccentricity) - EARTH_RADIUS_KM;
  const perigee = semiMajorAxis * (1 - elements.eccentricity) - EARTH_RADIUS_KM;
  
  return { apogee, perigee };
}

/**
 * Predict satellite position at future time using simplified SGP4
 */
export function predictPosition(
  currentState: SatelliteState, 
  targetTime: Date, 
  elements: OrbitalElements
): SatelliteState {
  const currentTime = currentState.timestamp;
  const deltaTime = (targetTime.getTime() - currentTime.getTime()) / 1000; // seconds
  
  if (deltaTime === 0) return currentState;
  
  // Simple Keplerian propagation (simplified for demonstration)
  const semiMajorAxis = calculateSemiMajorAxis(elements.meanMotion);
  const n = Math.sqrt(GRAVITATIONAL_PARAMETER / Math.pow(semiMajorAxis, 3)); // mean motion in rad/s
  
  // Update mean anomaly
  const newMeanAnomaly = (elements.meanAnomaly * Math.PI / 180 + n * deltaTime) % (2 * Math.PI);
  
  // Solve Kepler's equation (simplified)
  let E = newMeanAnomaly; // Initial guess
  for (let i = 0; i < 10; i++) {
    const E_new = newMeanAnomaly + elements.eccentricity * Math.sin(E);
    if (Math.abs(E_new - E) < 1e-10) break;
    E = E_new;
  }
  
  // True anomaly
  const nu = 2 * Math.atan2(
    Math.sqrt(1 + elements.eccentricity) * Math.sin(E / 2),
    Math.sqrt(1 - elements.eccentricity) * Math.cos(E / 2)
  );
  
  // Distance from Earth center
  const r = semiMajorAxis * (1 - elements.eccentricity * Math.cos(E));
  
  // Position in orbital plane
  const x_orbit = r * Math.cos(nu);
  const y_orbit = r * Math.sin(nu);
  
  // Rotation matrices for orbital elements
  const inc = elements.inclination * Math.PI / 180;
  const raan = elements.raan * Math.PI / 180;
  const argPer = elements.argOfPerigee * Math.PI / 180;
  
  // Transform to ECI coordinates
  const cosRaan = Math.cos(raan);
  const sinRaan = Math.sin(raan);
  const cosInc = Math.cos(inc);
  const sinInc = Math.sin(inc);
  const cosArgPer = Math.cos(argPer);
  const sinArgPer = Math.sin(argPer);
  
  const position: Position3D = {
    x: (cosRaan * cosArgPer - sinRaan * sinArgPer * cosInc) * x_orbit + 
       (-cosRaan * sinArgPer - sinRaan * cosArgPer * cosInc) * y_orbit,
    y: (sinRaan * cosArgPer + cosRaan * sinArgPer * cosInc) * x_orbit + 
       (-sinRaan * sinArgPer + cosRaan * cosArgPer * cosInc) * y_orbit,
    z: (sinInc * sinArgPer) * x_orbit + (sinInc * cosArgPer) * y_orbit
  };
  
  // Calculate velocity (simplified)
  const velocity: Velocity3D = {
    x: currentState.velocity.x, // Simplified - would need proper orbital mechanics
    y: currentState.velocity.y,
    z: currentState.velocity.z
  };
  
  // Calculate geodetic position
  const gmst = calculateGMST(targetTime);
  const geodetic = eciToGeodetic(position, gmst);
  
  return {
    position,
    velocity,
    geodetic,
    timestamp: targetTime
  };
}

/**
 * Calculate look angles (azimuth, elevation) from observer to satellite
 */
export function calculateLookAngles(
  observerGeodetic: GeodeticPosition,
  satellitePosition: Position3D,
  gmst: number
): { azimuth: number; elevation: number; range: number } {
  // Convert observer position to ECI
  const observerECI = geodeticToEci(observerGeodetic, gmst);
  
  // Range vector from observer to satellite
  const rangeVector = {
    x: satellitePosition.x - observerECI.x,
    y: satellitePosition.y - observerECI.y,
    z: satellitePosition.z - observerECI.z
  };
  
  const range = Math.sqrt(rangeVector.x * rangeVector.x + 
                         rangeVector.y * rangeVector.y + 
                         rangeVector.z * rangeVector.z);
  
  // Convert to topocentric coordinates
  const latRad = observerGeodetic.latitude * Math.PI / 180;
  const lonRad = observerGeodetic.longitude * Math.PI / 180;
  
  const sinLat = Math.sin(latRad);
  const cosLat = Math.cos(latRad);
  const sinLon = Math.sin(lonRad);
  const cosLon = Math.cos(lonRad);
  
  // Rotation to topocentric system
  const south = -sinLat * cosLon * rangeVector.x - sinLat * sinLon * rangeVector.y + cosLat * rangeVector.z;
  const east = -sinLon * rangeVector.x + cosLon * rangeVector.y;
  const up = cosLat * cosLon * rangeVector.x + cosLat * sinLon * rangeVector.y + sinLat * rangeVector.z;
  
  // Calculate azimuth and elevation
  const azimuth = Math.atan2(east, south) * 180 / Math.PI;
  const elevation = Math.atan2(up, Math.sqrt(south * south + east * east)) * 180 / Math.PI;
  
  return {
    azimuth: azimuth < 0 ? azimuth + 360 : azimuth,
    elevation,
    range
  };
}

/**
 * Calculate Doppler shift for satellite communication
 */
export function calculateDopplerShift(
  observerGeodetic: GeodeticPosition,
  satelliteState: SatelliteState,
  frequency: number,
  gmst: number
): number {
  const observerECI = geodeticToEci(observerGeodetic, gmst);
  
  // Range vector
  const rangeVector = {
    x: satelliteState.position.x - observerECI.x,
    y: satelliteState.position.y - observerECI.y,
    z: satelliteState.position.z - observerECI.z
  };
  
  const range = Math.sqrt(rangeVector.x * rangeVector.x + 
                         rangeVector.y * rangeVector.y + 
                         rangeVector.z * rangeVector.z);
  
  // Unit range vector
  const unitRange = {
    x: rangeVector.x / range,
    y: rangeVector.y / range,
    z: rangeVector.z / range
  };
  
  // Relative velocity projected along line of sight
  const relativeVelocity = satelliteState.velocity.x * unitRange.x + 
                          satelliteState.velocity.y * unitRange.y + 
                          satelliteState.velocity.z * unitRange.z;
  
  // Doppler shift
  return frequency * relativeVelocity / SPEED_OF_LIGHT * 1000; // Convert to m/s
}

/**
 * Check if satellite is in sunlight or shadow
 */
export function isInSunlight(position: Position3D, sunPosition: Position3D): boolean {
  // Simplified shadow calculation
  const earthRadius = EARTH_RADIUS_KM;
  const satelliteDistance = Math.sqrt(position.x * position.x + 
                                    position.y * position.y + 
                                    position.z * position.z);
  
  // Vector from Earth center to satellite
  const toSatellite = {
    x: position.x / satelliteDistance,
    y: position.y / satelliteDistance,
    z: position.z / satelliteDistance
  };
  
  // Vector from Earth center to Sun (normalized)
  const sunDistance = Math.sqrt(sunPosition.x * sunPosition.x + 
                               sunPosition.y * sunPosition.y + 
                               sunPosition.z * sunPosition.z);
  const toSun = {
    x: sunPosition.x / sunDistance,
    y: sunPosition.y / sunDistance,
    z: sunPosition.z / sunDistance
  };
  
  // Dot product
  const dotProduct = toSatellite.x * toSun.x + 
                    toSatellite.y * toSun.y + 
                    toSatellite.z * toSun.z;
  
  // If satellite is on the night side and within Earth's shadow cone
  if (dotProduct < 0) {
    const shadowAngle = Math.asin(earthRadius / satelliteDistance);
    const sunAngle = Math.acos(-dotProduct);
    return sunAngle > shadowAngle;
  }
  
  return true; // On day side
}

/**
 * Format orbital elements for display
 */
export function formatOrbitalElements(elements: OrbitalElements): Record<string, string> {
  const { apogee, perigee } = calculateApogeePerigee(elements);
  const period = calculateOrbitalPeriod(calculateSemiMajorAxis(elements.meanMotion));
  
  return {
    'Inclination': `${elements.inclination.toFixed(4)}°`,
    'Eccentricity': elements.eccentricity.toFixed(6),
    'RAAN': `${elements.raan.toFixed(4)}°`,
    'Arg. of Perigee': `${elements.argOfPerigee.toFixed(4)}°`,
    'Mean Anomaly': `${elements.meanAnomaly.toFixed(4)}°`,
    'Mean Motion': `${elements.meanMotion.toFixed(6)} rev/day`,
    'Apogee': `${apogee.toFixed(2)} km`,
    'Perigee': `${perigee.toFixed(2)} km`,
    'Period': `${(period / 60).toFixed(2)} min`
  };
}