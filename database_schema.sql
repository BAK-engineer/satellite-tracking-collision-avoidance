-- Live Orbital Ballet - Comprehensive Database Schema
-- PostgreSQL 15.0 Schema for Satellite Tracking System

-- Enable extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- Drop existing tables if they exist (for development)
DROP TABLE IF EXISTS collision_predictions CASCADE;
DROP TABLE IF EXISTS maneuver_plans CASCADE;
DROP TABLE IF EXISTS risk_assessments CASCADE;
DROP TABLE IF EXISTS orbital_states CASCADE;
DROP TABLE IF EXISTS debris_objects CASCADE;
DROP TABLE IF EXISTS satellites CASCADE;
DROP TABLE IF EXISTS tle_data CASCADE;
DROP TABLE IF EXISTS system_logs CASCADE;
DROP TABLE IF EXISTS user_sessions CASCADE;

-- =============================================
-- CORE TABLES
-- =============================================

-- TLE (Two-Line Element) Data Table
CREATE TABLE tle_data (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    norad_id INTEGER NOT NULL UNIQUE,
    satellite_name VARCHAR(255) NOT NULL,
    line1 TEXT NOT NULL,
    line2 TEXT NOT NULL,
    classification CHAR(1) DEFAULT 'U', -- U=Unclassified, C=Classified, S=Secret
    launch_year INTEGER,
    launch_number INTEGER,
    piece_designator VARCHAR(3),
    epoch_year INTEGER,
    epoch_day DECIMAL(12,8),
    first_derivative_mean_motion DECIMAL(10,8),
    second_derivative_mean_motion DECIMAL(5,5),
    bstar_drag_term DECIMAL(5,5),
    element_set_number INTEGER,
    checksum1 INTEGER,
    checksum2 INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    data_source VARCHAR(100) DEFAULT 'CELESTRAK',
    
    -- Constraints
    CONSTRAINT valid_norad_id CHECK (norad_id > 0),
    CONSTRAINT valid_classification CHECK (classification IN ('U', 'C', 'S'))
);

-- Satellites Table (Active satellites with metadata)
CREATE TABLE satellites (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    norad_id INTEGER NOT NULL REFERENCES tle_data(norad_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    country_code CHAR(3),
    launch_date DATE,
    satellite_type VARCHAR(50), -- 'weather', 'communication', 'navigation', 'military', 'scientific'
    operational_status VARCHAR(20) DEFAULT 'ACTIVE', -- 'ACTIVE', 'INACTIVE', 'DECAYED', 'UNKNOWN'
    mass_kg DECIMAL(10,2),
    dimensions_m VARCHAR(100), -- e.g., "2.5x1.8x1.2"
    power_watts DECIMAL(8,2),
    orbital_regime VARCHAR(20), -- 'LEO', 'MEO', 'GEO', 'HEO', 'SSO'
    mission_description TEXT,
    owner_operator VARCHAR(255),
    
    -- Tracking preferences
    priority_level INTEGER DEFAULT 5 CHECK (priority_level BETWEEN 1 AND 10),
    track_continuously BOOLEAN DEFAULT TRUE,
    collision_monitoring BOOLEAN DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_tracked TIMESTAMP WITH TIME ZONE,
    
    CONSTRAINT valid_satellite_type CHECK (satellite_type IN 
        ('weather', 'communication', 'navigation', 'military', 'scientific', 'commercial', 'experimental')),
    CONSTRAINT valid_operational_status CHECK (operational_status IN 
        ('ACTIVE', 'INACTIVE', 'DECAYED', 'UNKNOWN', 'DEORBITED'))
);

-- Space Debris Objects Table
CREATE TABLE debris_objects (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    debris_id VARCHAR(50) NOT NULL UNIQUE,
    source_satellite_id UUID REFERENCES satellites(id),
    debris_type VARCHAR(50), -- 'fragment', 'intact_body', 'rocket_body', 'mission_related', 'unknown'
    estimated_size_m DECIMAL(8,3),
    estimated_mass_kg DECIMAL(10,2),
    creation_date DATE,
    decay_prediction_date DATE,
    
    -- Risk Classification
    risk_category VARCHAR(20) DEFAULT 'MEDIUM', -- 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
    collision_probability DECIMAL(8,6) DEFAULT 0.0,
    
    -- Tracking status
    tracking_status VARCHAR(20) DEFAULT 'MONITORED', -- 'MONITORED', 'TRACKED', 'LOST', 'DECAYED'
    last_observed TIMESTAMP WITH TIME ZONE,
    observation_count INTEGER DEFAULT 0,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_debris_type CHECK (debris_type IN 
        ('fragment', 'intact_body', 'rocket_body', 'mission_related', 'unknown')),
    CONSTRAINT valid_risk_category CHECK (risk_category IN 
        ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    CONSTRAINT valid_tracking_status CHECK (tracking_status IN 
        ('MONITORED', 'TRACKED', 'LOST', 'DECAYED'))
);

-- =============================================
-- ORBITAL DATA TABLES
-- =============================================

-- Orbital States Table (Position and velocity data over time)
CREATE TABLE orbital_states (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    object_type VARCHAR(20) NOT NULL, -- 'SATELLITE', 'DEBRIS'
    object_id UUID NOT NULL, -- References satellites.id or debris_objects.id
    norad_id INTEGER, -- For satellites
    
    -- Position (ECI coordinates in km)
    position_x DECIMAL(15,6) NOT NULL,
    position_y DECIMAL(15,6) NOT NULL,
    position_z DECIMAL(15,6) NOT NULL,
    
    -- Velocity (ECI coordinates in km/s)
    velocity_x DECIMAL(12,9) NOT NULL,
    velocity_y DECIMAL(12,9) NOT NULL,
    velocity_z DECIMAL(12,9) NOT NULL,
    
    -- Computed orbital elements
    semi_major_axis_km DECIMAL(15,6),
    eccentricity DECIMAL(10,8),
    inclination_deg DECIMAL(8,5),
    longitude_ascending_deg DECIMAL(8,5),
    argument_perigee_deg DECIMAL(8,5),
    mean_anomaly_deg DECIMAL(8,5),
    
    -- Derived properties
    altitude_km DECIMAL(10,3),
    orbital_period_sec DECIMAL(12,3),
    apogee_km DECIMAL(10,3),
    perigee_km DECIMAL(10,3),
    
    -- Timing and metadata
    epoch TIMESTAMP WITH TIME ZONE NOT NULL,
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    prediction_type VARCHAR(20) DEFAULT 'SGP4', -- 'SGP4', 'NUMERICAL', 'ANALYTICAL'
    accuracy_estimate_km DECIMAL(8,3),
    error_flag BOOLEAN DEFAULT FALSE,
    
    CONSTRAINT valid_object_type CHECK (object_type IN ('SATELLITE', 'DEBRIS')),
    CONSTRAINT valid_prediction_type CHECK (prediction_type IN ('SGP4', 'NUMERICAL', 'ANALYTICAL'))
);

-- =============================================
-- RISK AND COLLISION TABLES
-- =============================================

-- Risk Assessments Table
CREATE TABLE risk_assessments (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    primary_object_type VARCHAR(20) NOT NULL,
    primary_object_id UUID NOT NULL,
    secondary_object_type VARCHAR(20) NOT NULL,
    secondary_object_id UUID NOT NULL,
    
    -- Risk metrics
    collision_probability DECIMAL(8,6) NOT NULL,
    miss_distance_km DECIMAL(10,6),
    relative_velocity_kms DECIMAL(8,3),
    time_to_closest_approach TIMESTAMP WITH TIME ZONE,
    
    -- Risk features (for AI model)
    approach_angle_deg DECIMAL(6,2),
    altitude_diff_km DECIMAL(8,3),
    inclination_diff_deg DECIMAL(6,2),
    combined_mass_factor DECIMAL(6,3),
    atmospheric_density_factor DECIMAL(6,4),
    
    -- AI Assessment
    physics_risk_score DECIMAL(6,4),
    ml_risk_score DECIMAL(6,4),
    hybrid_risk_score DECIMAL(6,4),
    risk_category VARCHAR(20),
    confidence_level DECIMAL(4,3),
    
    -- Assessment metadata
    assessment_method VARCHAR(50) DEFAULT 'HYBRID_AI',
    model_version VARCHAR(20),
    computed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    valid_until TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    
    CONSTRAINT valid_primary_object_type CHECK (primary_object_type IN ('SATELLITE', 'DEBRIS')),
    CONSTRAINT valid_secondary_object_type CHECK (secondary_object_type IN ('SATELLITE', 'DEBRIS')),
    CONSTRAINT valid_risk_category_assessment CHECK (risk_category IN 
        ('MINIMAL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'))
);

-- Collision Predictions Table
CREATE TABLE collision_predictions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    risk_assessment_id UUID REFERENCES risk_assessments(id) ON DELETE CASCADE,
    
    -- Collision details
    predicted_collision_time TIMESTAMP WITH TIME ZONE NOT NULL,
    collision_probability DECIMAL(8,6) NOT NULL,
    miss_distance_km DECIMAL(10,6),
    
    -- Collision location (ECI coordinates)
    predicted_position_x DECIMAL(15,6),
    predicted_position_y DECIMAL(15,6),
    predicted_position_z DECIMAL(15,6),
    
    -- Impact characteristics
    relative_velocity_kms DECIMAL(8,3),
    impact_energy_joules DECIMAL(15,2),
    debris_generation_estimate INTEGER,
    
    -- Prediction metadata
    prediction_window_hours DECIMAL(6,2) DEFAULT 72.0,
    uncertainty_km DECIMAL(8,3),
    confidence_level DECIMAL(4,3),
    
    -- Status
    status VARCHAR(20) DEFAULT 'ACTIVE', -- 'ACTIVE', 'RESOLVED', 'EXPIRED', 'FALSE_ALARM'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_prediction_status CHECK (status IN 
        ('ACTIVE', 'RESOLVED', 'EXPIRED', 'FALSE_ALARM', 'UNDER_REVIEW'))
);

-- =============================================
-- MANEUVER PLANNING TABLES
-- =============================================

-- Maneuver Plans Table
CREATE TABLE maneuver_plans (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    collision_prediction_id UUID REFERENCES collision_predictions(id) ON DELETE CASCADE,
    satellite_id UUID NOT NULL REFERENCES satellites(id),
    
    -- Maneuver details
    maneuver_type VARCHAR(30) NOT NULL,
    execution_time TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Delta-V components (m/s)
    delta_v_radial DECIMAL(10,6),
    delta_v_tangential DECIMAL(10,6),
    delta_v_normal DECIMAL(10,6),
    delta_v_total DECIMAL(10,6) NOT NULL,
    
    -- Thrust vector (unit vector in ECI)
    thrust_direction_x DECIMAL(10,8),
    thrust_direction_y DECIMAL(10,8),
    thrust_direction_z DECIMAL(10,8),
    
    -- Execution parameters
    burn_duration_sec DECIMAL(8,2),
    required_thrust_n DECIMAL(10,4),
    fuel_consumption_kg DECIMAL(8,3),
    
    -- Success metrics
    success_probability DECIMAL(4,3),
    risk_reduction_factor DECIMAL(4,3),
    new_miss_distance_km DECIMAL(10,6),
    
    -- Implementation details
    complexity_level VARCHAR(20) DEFAULT 'MODERATE',
    implementation_status VARCHAR(20) DEFAULT 'PLANNED',
    approval_required BOOLEAN DEFAULT TRUE,
    
    -- Timing constraints
    decision_deadline TIMESTAMP WITH TIME ZONE,
    execution_window_start TIMESTAMP WITH TIME ZONE,
    execution_window_end TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by VARCHAR(100),
    
    CONSTRAINT valid_maneuver_type CHECK (maneuver_type IN 
        ('RADIAL_IN', 'RADIAL_OUT', 'TANGENTIAL_PROGRADE', 'TANGENTIAL_RETROGRADE', 
         'NORMAL_POSITIVE', 'NORMAL_NEGATIVE', 'COMBINED')),
    CONSTRAINT valid_complexity_level CHECK (complexity_level IN 
        ('SIMPLE', 'MODERATE', 'COMPLEX', 'CRITICAL')),
    CONSTRAINT valid_implementation_status CHECK (implementation_status IN 
        ('PLANNED', 'APPROVED', 'SCHEDULED', 'EXECUTING', 'COMPLETED', 'FAILED', 'CANCELLED'))
);

-- =============================================
-- SYSTEM AND LOGGING TABLES
-- =============================================

-- System Logs Table
CREATE TABLE system_logs (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    log_level VARCHAR(10) NOT NULL,
    component VARCHAR(50) NOT NULL,
    message TEXT NOT NULL,
    details JSONB,
    
    -- Context
    object_type VARCHAR(20),
    object_id UUID,
    user_session_id UUID,
    
    -- Timing
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    duration_ms INTEGER,
    
    -- Classification
    category VARCHAR(30), -- 'DATA_FETCH', 'RISK_ASSESSMENT', 'MANEUVER_PLANNING', 'SYSTEM'
    severity VARCHAR(20) DEFAULT 'INFO',
    
    CONSTRAINT valid_log_level CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    CONSTRAINT valid_severity CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL'))
);

-- User Sessions Table (for tracking dashboard usage)
CREATE TABLE user_sessions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    session_token VARCHAR(255) NOT NULL UNIQUE,
    user_identifier VARCHAR(100), -- IP address or user ID
    
    -- Session data
    start_time TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    end_time TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Usage metrics
    page_views INTEGER DEFAULT 0,
    actions_performed INTEGER DEFAULT 0,
    data_queries INTEGER DEFAULT 0,
    
    -- Client info
    user_agent TEXT,
    ip_address INET,
    browser_info JSONB,
    
    CONSTRAINT valid_session_duration CHECK (end_time IS NULL OR end_time >= start_time)
);

-- =============================================
-- INDEXES FOR PERFORMANCE
-- =============================================

-- TLE Data Indexes
CREATE INDEX idx_tle_norad_id ON tle_data(norad_id);
CREATE INDEX idx_tle_active ON tle_data(is_active);
CREATE INDEX idx_tle_updated ON tle_data(updated_at);
CREATE INDEX idx_tle_source ON tle_data(data_source);

-- Satellites Indexes
CREATE INDEX idx_satellites_norad ON satellites(norad_id);
CREATE INDEX idx_satellites_type ON satellites(satellite_type);
CREATE INDEX idx_satellites_status ON satellites(operational_status);
CREATE INDEX idx_satellites_priority ON satellites(priority_level);
CREATE INDEX idx_satellites_regime ON satellites(orbital_regime);

-- Debris Indexes
CREATE INDEX idx_debris_risk ON debris_objects(risk_category);
CREATE INDEX idx_debris_type ON debris_objects(debris_type);
CREATE INDEX idx_debris_status ON debris_objects(tracking_status);
CREATE INDEX idx_debris_observed ON debris_objects(last_observed);

-- Orbital States Indexes
CREATE INDEX idx_orbital_object ON orbital_states(object_type, object_id);
CREATE INDEX idx_orbital_norad ON orbital_states(norad_id);
CREATE INDEX idx_orbital_epoch ON orbital_states(epoch);
CREATE INDEX idx_orbital_computed ON orbital_states(computed_at);
CREATE INDEX idx_orbital_altitude ON orbital_states(altitude_km);

-- Risk Assessment Indexes
CREATE INDEX idx_risk_primary ON risk_assessments(primary_object_type, primary_object_id);
CREATE INDEX idx_risk_secondary ON risk_assessments(secondary_object_type, secondary_object_id);
CREATE INDEX idx_risk_probability ON risk_assessments(collision_probability);
CREATE INDEX idx_risk_category ON risk_assessments(risk_category);
CREATE INDEX idx_risk_active ON risk_assessments(is_active);
CREATE INDEX idx_risk_computed ON risk_assessments(computed_at);

-- Collision Predictions Indexes
CREATE INDEX idx_collision_time ON collision_predictions(predicted_collision_time);
CREATE INDEX idx_collision_probability ON collision_predictions(collision_probability);
CREATE INDEX idx_collision_status ON collision_predictions(status);
CREATE INDEX idx_collision_created ON collision_predictions(created_at);

-- Maneuver Plans Indexes
CREATE INDEX idx_maneuver_satellite ON maneuver_plans(satellite_id);
CREATE INDEX idx_maneuver_execution ON maneuver_plans(execution_time);
CREATE INDEX idx_maneuver_status ON maneuver_plans(implementation_status);
CREATE INDEX idx_maneuver_type ON maneuver_plans(maneuver_type);
CREATE INDEX idx_maneuver_created ON maneuver_plans(created_at);

-- System Logs Indexes
CREATE INDEX idx_logs_timestamp ON system_logs(timestamp);
CREATE INDEX idx_logs_component ON system_logs(component);
CREATE INDEX idx_logs_level ON system_logs(log_level);
CREATE INDEX idx_logs_category ON system_logs(category);
CREATE INDEX idx_logs_object ON system_logs(object_type, object_id);

-- User Sessions Indexes
CREATE INDEX idx_sessions_active ON user_sessions(is_active);
CREATE INDEX idx_sessions_token ON user_sessions(session_token);
CREATE INDEX idx_sessions_start ON user_sessions(start_time);
CREATE INDEX idx_sessions_activity ON user_sessions(last_activity);

-- =============================================
-- VIEWS FOR COMMON QUERIES
-- =============================================

-- Active High-Risk Objects View
CREATE VIEW v_high_risk_objects AS
SELECT 
    'SATELLITE' as object_type,
    s.id,
    s.norad_id,
    s.name,
    s.satellite_type,
    s.orbital_regime,
    COUNT(ra.id) as active_risk_assessments,
    MAX(ra.collision_probability) as max_collision_probability,
    MAX(ra.hybrid_risk_score) as max_risk_score
FROM satellites s
LEFT JOIN risk_assessments ra ON (
    (ra.primary_object_type = 'SATELLITE' AND ra.primary_object_id = s.id) OR
    (ra.secondary_object_type = 'SATELLITE' AND ra.secondary_object_id = s.id)
) AND ra.is_active = true
WHERE s.operational_status = 'ACTIVE'
GROUP BY s.id, s.norad_id, s.name, s.satellite_type, s.orbital_regime
HAVING COUNT(ra.id) > 0 OR MAX(ra.collision_probability) > 0.01

UNION ALL

SELECT 
    'DEBRIS' as object_type,
    d.id,
    NULL as norad_id,
    d.debris_id as name,
    d.debris_type,
    NULL as orbital_regime,
    COUNT(ra.id) as active_risk_assessments,
    MAX(ra.collision_probability) as max_collision_probability,
    MAX(ra.hybrid_risk_score) as max_risk_score
FROM debris_objects d
LEFT JOIN risk_assessments ra ON (
    (ra.primary_object_type = 'DEBRIS' AND ra.primary_object_id = d.id) OR
    (ra.secondary_object_type = 'DEBRIS' AND ra.secondary_object_id = d.id)
) AND ra.is_active = true
WHERE d.tracking_status IN ('MONITORED', 'TRACKED')
GROUP BY d.id, d.debris_id, d.debris_type
HAVING COUNT(ra.id) > 0 OR MAX(ra.collision_probability) > 0.01;

-- Current Orbital Positions View
CREATE VIEW v_current_positions AS
WITH latest_states AS (
    SELECT DISTINCT ON (object_type, object_id)
        object_type,
        object_id,
        norad_id,
        position_x,
        position_y,
        position_z,
        velocity_x,
        velocity_y,
        velocity_z,
        altitude_km,
        epoch,
        computed_at
    FROM orbital_states
    ORDER BY object_type, object_id, computed_at DESC
)
SELECT 
    ls.*,
    CASE 
        WHEN ls.object_type = 'SATELLITE' THEN s.name
        WHEN ls.object_type = 'DEBRIS' THEN d.debris_id
    END as object_name,
    CASE 
        WHEN ls.object_type = 'SATELLITE' THEN s.satellite_type
        WHEN ls.object_type = 'DEBRIS' THEN d.debris_type
    END as object_subtype
FROM latest_states ls
LEFT JOIN satellites s ON ls.object_type = 'SATELLITE' AND ls.object_id = s.id
LEFT JOIN debris_objects d ON ls.object_type = 'DEBRIS' AND ls.object_id = d.id;

-- Active Collision Alerts View
CREATE VIEW v_active_collision_alerts AS
SELECT 
    cp.id,
    cp.predicted_collision_time,
    cp.collision_probability,
    cp.miss_distance_km,
    cp.relative_velocity_kms,
    ra.primary_object_type,
    ra.primary_object_id,
    ra.secondary_object_type, 
    ra.secondary_object_id,
    ra.hybrid_risk_score,
    ra.risk_category,
    EXTRACT(EPOCH FROM (cp.predicted_collision_time - NOW()))/3600 as hours_to_collision,
    mp.implementation_status as maneuver_status,
    mp.delta_v_total as planned_delta_v
FROM collision_predictions cp
JOIN risk_assessments ra ON cp.risk_assessment_id = ra.id
LEFT JOIN maneuver_plans mp ON cp.id = mp.collision_prediction_id
WHERE cp.status = 'ACTIVE' 
    AND cp.predicted_collision_time > NOW()
    AND cp.predicted_collision_time < NOW() + INTERVAL '7 days'
ORDER BY cp.collision_probability DESC, cp.predicted_collision_time ASC;

-- =============================================
-- TRIGGERS AND FUNCTIONS
-- =============================================

-- Function to update updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_tle_data_updated_at BEFORE UPDATE ON tle_data 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_satellites_updated_at BEFORE UPDATE ON satellites 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_debris_objects_updated_at BEFORE UPDATE ON debris_objects 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_collision_predictions_updated_at BEFORE UPDATE ON collision_predictions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_maneuver_plans_updated_at BEFORE UPDATE ON maneuver_plans 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Function to log risk assessment changes
CREATE OR REPLACE FUNCTION log_risk_assessment_changes()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'UPDATE' THEN
        IF OLD.collision_probability != NEW.collision_probability OR 
           OLD.risk_category != NEW.risk_category THEN
            INSERT INTO system_logs (log_level, component, message, details, category)
            VALUES (
                'INFO',
                'RISK_ASSESSMENT',
                'Risk assessment updated for objects',
                jsonb_build_object(
                    'risk_assessment_id', NEW.id,
                    'old_probability', OLD.collision_probability,
                    'new_probability', NEW.collision_probability,
                    'old_category', OLD.risk_category,
                    'new_category', NEW.risk_category
                ),
                'RISK_ASSESSMENT'
            );
        END IF;
    END IF;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER log_risk_changes AFTER UPDATE ON risk_assessments
    FOR EACH ROW EXECUTE FUNCTION log_risk_assessment_changes();

-- =============================================
-- SAMPLE DATA INSERTION
-- =============================================

-- Insert some sample data for testing
INSERT INTO tle_data (norad_id, satellite_name, line1, line2, data_source) VALUES 
(25544, 'ISS (ZARYA)', 
 '1 25544U 98067A   23001.00000000  .00002182  00000-0  40768-4 0  9992',
 '2 25544  51.6461 339.2377 0006317  69.9862  25.2906 15.48919103123456',
 'CELESTRAK'),
(43013, 'STARLINK-1007',
 '1 43013U 17083B   23001.00000000  .00001743  00000-0  13359-3 0  9993',
 '2 43013  53.0014 290.3456 0001234  89.1234 270.9876 15.06142345234567',
 'CELESTRAK'),
(41168, 'NOAA-20',
 '1 41168U 17073A   23001.00000000  .00000123  00000-0  63428-4 0  9994',
 '2 41168  98.7123 123.4567 0001456 178.9012   1.2345 14.19554321345678',
 'CELESTRAK');

-- Create a database initialization script info
INSERT INTO system_logs (log_level, component, message, category) 
VALUES ('INFO', 'DATABASE', 'Live Orbital Ballet database schema initialized successfully', 'SYSTEM');

-- Create a comment with schema version
COMMENT ON DATABASE postgres IS 'Live Orbital Ballet v1.0 - Satellite Tracking System Database';