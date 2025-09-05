"""
Live Orbital Ballet - Database Models
SQLAlchemy ORM models for the satellite tracking system
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional, List
import uuid

from sqlalchemy import (
    create_engine, Column, String, Integer, DateTime, Boolean, 
    Numeric, Text, ForeignKey, CheckConstraint, Index, JSON
)
from sqlalchemy.dialects.postgresql import UUID, INET, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func

# Database base class
Base = declarative_base()

class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(DateTime(timezone=True), default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=func.now(), onupdate=func.now(), nullable=False)

class TLEData(Base, TimestampMixin):
    """Two-Line Element data for satellites"""
    __tablename__ = 'tle_data'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    norad_id = Column(Integer, unique=True, nullable=False, index=True)
    satellite_name = Column(String(255), nullable=False)
    line1 = Column(Text, nullable=False)
    line2 = Column(Text, nullable=False)
    classification = Column(String(1), default='U')
    launch_year = Column(Integer)
    launch_number = Column(Integer)
    piece_designator = Column(String(3))
    epoch_year = Column(Integer)
    epoch_day = Column(Numeric(12, 8))
    first_derivative_mean_motion = Column(Numeric(10, 8))
    second_derivative_mean_motion = Column(Numeric(5, 5))
    bstar_drag_term = Column(Numeric(5, 5))
    element_set_number = Column(Integer)
    checksum1 = Column(Integer)
    checksum2 = Column(Integer)
    is_active = Column(Boolean, default=True, index=True)
    data_source = Column(String(100), default='CELESTRAK', index=True)
    
    # Relationships
    satellites = relationship("Satellite", back_populates="tle_data", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint('norad_id > 0', name='valid_norad_id'),
        CheckConstraint("classification IN ('U', 'C', 'S')", name='valid_classification'),
        Index('idx_tle_updated', 'updated_at'),
    )
    
    def __repr__(self):
        return f"<TLEData(norad_id={self.norad_id}, name='{self.satellite_name}')>"

class Satellite(Base, TimestampMixin):
    """Active satellites with metadata"""
    __tablename__ = 'satellites'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    norad_id = Column(Integer, ForeignKey('tle_data.norad_id', ondelete='CASCADE'), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    country_code = Column(String(3))
    launch_date = Column(DateTime(timezone=True))
    satellite_type = Column(String(50), index=True)
    operational_status = Column(String(20), default='ACTIVE', index=True)
    mass_kg = Column(Numeric(10, 2))
    dimensions_m = Column(String(100))
    power_watts = Column(Numeric(8, 2))
    orbital_regime = Column(String(20), index=True)
    mission_description = Column(Text)
    owner_operator = Column(String(255))
    
    # Tracking preferences
    priority_level = Column(Integer, default=5, index=True)
    track_continuously = Column(Boolean, default=True)
    collision_monitoring = Column(Boolean, default=True)
    
    # Tracking status
    last_tracked = Column(DateTime(timezone=True))
    
    # Relationships
    tle_data = relationship("TLEData", back_populates="satellites")
    orbital_states = relationship("OrbitalState", back_populates="satellite", cascade="all, delete-orphan")
    maneuver_plans = relationship("ManeuverPlan", back_populates="satellite", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "satellite_type IN ('weather', 'communication', 'navigation', 'military', 'scientific', 'commercial', 'experimental')",
            name='valid_satellite_type'
        ),
        CheckConstraint(
            "operational_status IN ('ACTIVE', 'INACTIVE', 'DECAYED', 'UNKNOWN', 'DEORBITED')",
            name='valid_operational_status'
        ),
        CheckConstraint('priority_level BETWEEN 1 AND 10', name='valid_priority_level'),
    )
    
    def __repr__(self):
        return f"<Satellite(norad_id={self.norad_id}, name='{self.name}', type='{self.satellite_type}')>"

class DebrisObject(Base, TimestampMixin):
    """Space debris objects"""
    __tablename__ = 'debris_objects'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    debris_id = Column(String(50), unique=True, nullable=False)
    source_satellite_id = Column(UUID(as_uuid=True), ForeignKey('satellites.id'))
    debris_type = Column(String(50), index=True)
    estimated_size_m = Column(Numeric(8, 3))
    estimated_mass_kg = Column(Numeric(10, 2))
    creation_date = Column(DateTime(timezone=True))
    decay_prediction_date = Column(DateTime(timezone=True))
    
    # Risk Classification
    risk_category = Column(String(20), default='MEDIUM', index=True)
    collision_probability = Column(Numeric(8, 6), default=0.0)
    
    # Tracking status
    tracking_status = Column(String(20), default='MONITORED', index=True)
    last_observed = Column(DateTime(timezone=True), index=True)
    observation_count = Column(Integer, default=0)
    
    # Relationships
    source_satellite = relationship("Satellite")
    orbital_states = relationship("OrbitalState", back_populates="debris", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "debris_type IN ('fragment', 'intact_body', 'rocket_body', 'mission_related', 'unknown')",
            name='valid_debris_type'
        ),
        CheckConstraint(
            "risk_category IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name='valid_risk_category'
        ),
        CheckConstraint(
            "tracking_status IN ('MONITORED', 'TRACKED', 'LOST', 'DECAYED')",
            name='valid_tracking_status'
        ),
    )
    
    def __repr__(self):
        return f"<DebrisObject(debris_id='{self.debris_id}', type='{self.debris_type}', risk='{self.risk_category}')>"

class OrbitalState(Base):
    """Position and velocity data over time"""
    __tablename__ = 'orbital_states'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    object_type = Column(String(20), nullable=False, index=True)
    object_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    norad_id = Column(Integer, index=True)
    
    # Position (ECI coordinates in km)
    position_x = Column(Numeric(15, 6), nullable=False)
    position_y = Column(Numeric(15, 6), nullable=False)
    position_z = Column(Numeric(15, 6), nullable=False)
    
    # Velocity (ECI coordinates in km/s)
    velocity_x = Column(Numeric(12, 9), nullable=False)
    velocity_y = Column(Numeric(12, 9), nullable=False)
    velocity_z = Column(Numeric(12, 9), nullable=False)
    
    # Computed orbital elements
    semi_major_axis_km = Column(Numeric(15, 6))
    eccentricity = Column(Numeric(10, 8))
    inclination_deg = Column(Numeric(8, 5))
    longitude_ascending_deg = Column(Numeric(8, 5))
    argument_perigee_deg = Column(Numeric(8, 5))
    mean_anomaly_deg = Column(Numeric(8, 5))
    
    # Derived properties
    altitude_km = Column(Numeric(10, 3), index=True)
    orbital_period_sec = Column(Numeric(12, 3))
    apogee_km = Column(Numeric(10, 3))
    perigee_km = Column(Numeric(10, 3))
    
    # Timing and metadata
    epoch = Column(DateTime(timezone=True), nullable=False, index=True)
    computed_at = Column(DateTime(timezone=True), default=func.now(), index=True)
    prediction_type = Column(String(20), default='SGP4')
    accuracy_estimate_km = Column(Numeric(8, 3))
    error_flag = Column(Boolean, default=False)
    
    # Relationships (using foreign keys for specific object types)
    satellite = relationship("Satellite", back_populates="orbital_states", 
                           foreign_keys=[object_id], 
                           primaryjoin="and_(OrbitalState.object_id==Satellite.id, OrbitalState.object_type=='SATELLITE')")
    debris = relationship("DebrisObject", back_populates="orbital_states",
                         foreign_keys=[object_id],
                         primaryjoin="and_(OrbitalState.object_id==DebrisObject.id, OrbitalState.object_type=='DEBRIS')")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("object_type IN ('SATELLITE', 'DEBRIS')", name='valid_object_type'),
        CheckConstraint("prediction_type IN ('SGP4', 'NUMERICAL', 'ANALYTICAL')", name='valid_prediction_type'),
        Index('idx_orbital_object', 'object_type', 'object_id'),
    )
    
    @property
    def position_vector(self):
        """Position as a tuple (x, y, z)"""
        return (float(self.position_x), float(self.position_y), float(self.position_z))
    
    @property
    def velocity_vector(self):
        """Velocity as a tuple (vx, vy, vz)"""
        return (float(self.velocity_x), float(self.velocity_y), float(self.velocity_z))
    
    def __repr__(self):
        return f"<OrbitalState(object_type='{self.object_type}', altitude={self.altitude_km}km, epoch='{self.epoch}')>"

class RiskAssessment(Base, TimestampMixin):
    """Risk assessments between objects"""
    __tablename__ = 'risk_assessments'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    primary_object_type = Column(String(20), nullable=False, index=True)
    primary_object_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    secondary_object_type = Column(String(20), nullable=False, index=True)
    secondary_object_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Risk metrics
    collision_probability = Column(Numeric(8, 6), nullable=False, index=True)
    miss_distance_km = Column(Numeric(10, 6))
    relative_velocity_kms = Column(Numeric(8, 3))
    time_to_closest_approach = Column(DateTime(timezone=True))
    
    # Risk features (for AI model)
    approach_angle_deg = Column(Numeric(6, 2))
    altitude_diff_km = Column(Numeric(8, 3))
    inclination_diff_deg = Column(Numeric(6, 2))
    combined_mass_factor = Column(Numeric(6, 3))
    atmospheric_density_factor = Column(Numeric(6, 4))
    
    # AI Assessment
    physics_risk_score = Column(Numeric(6, 4))
    ml_risk_score = Column(Numeric(6, 4))
    hybrid_risk_score = Column(Numeric(6, 4))
    risk_category = Column(String(20), index=True)
    confidence_level = Column(Numeric(4, 3))
    
    # Assessment metadata
    assessment_method = Column(String(50), default='HYBRID_AI')
    model_version = Column(String(20))
    computed_at = Column(DateTime(timezone=True), default=func.now(), index=True)
    valid_until = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, index=True)
    
    # Relationships
    collision_predictions = relationship("CollisionPrediction", back_populates="risk_assessment", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("primary_object_type IN ('SATELLITE', 'DEBRIS')", name='valid_primary_object_type'),
        CheckConstraint("secondary_object_type IN ('SATELLITE', 'DEBRIS')", name='valid_secondary_object_type'),
        CheckConstraint(
            "risk_category IN ('MINIMAL', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL')",
            name='valid_risk_category_assessment'
        ),
        Index('idx_risk_primary', 'primary_object_type', 'primary_object_id'),
        Index('idx_risk_secondary', 'secondary_object_type', 'secondary_object_id'),
    )
    
    def __repr__(self):
        return f"<RiskAssessment(probability={self.collision_probability}, category='{self.risk_category}')>"

class CollisionPrediction(Base, TimestampMixin):
    """Collision predictions"""
    __tablename__ = 'collision_predictions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    risk_assessment_id = Column(UUID(as_uuid=True), ForeignKey('risk_assessments.id', ondelete='CASCADE'), nullable=False)
    
    # Collision details
    predicted_collision_time = Column(DateTime(timezone=True), nullable=False, index=True)
    collision_probability = Column(Numeric(8, 6), nullable=False, index=True)
    miss_distance_km = Column(Numeric(10, 6))
    
    # Collision location (ECI coordinates)
    predicted_position_x = Column(Numeric(15, 6))
    predicted_position_y = Column(Numeric(15, 6))
    predicted_position_z = Column(Numeric(15, 6))
    
    # Impact characteristics
    relative_velocity_kms = Column(Numeric(8, 3))
    impact_energy_joules = Column(Numeric(15, 2))
    debris_generation_estimate = Column(Integer)
    
    # Prediction metadata
    prediction_window_hours = Column(Numeric(6, 2), default=72.0)
    uncertainty_km = Column(Numeric(8, 3))
    confidence_level = Column(Numeric(4, 3))
    
    # Status
    status = Column(String(20), default='ACTIVE', index=True)
    
    # Relationships
    risk_assessment = relationship("RiskAssessment", back_populates="collision_predictions")
    maneuver_plans = relationship("ManeuverPlan", back_populates="collision_prediction", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('ACTIVE', 'RESOLVED', 'EXPIRED', 'FALSE_ALARM', 'UNDER_REVIEW')",
            name='valid_prediction_status'
        ),
    )
    
    @property
    def predicted_position_vector(self):
        """Predicted collision position as a tuple (x, y, z)"""
        if all(p is not None for p in [self.predicted_position_x, self.predicted_position_y, self.predicted_position_z]):
            return (float(self.predicted_position_x), float(self.predicted_position_y), float(self.predicted_position_z))
        return None
    
    @property
    def hours_to_collision(self):
        """Hours until predicted collision"""
        if self.predicted_collision_time:
            delta = self.predicted_collision_time - datetime.now(timezone.utc)
            return delta.total_seconds() / 3600
        return None
    
    def __repr__(self):
        return f"<CollisionPrediction(time='{self.predicted_collision_time}', probability={self.collision_probability})>"

class ManeuverPlan(Base, TimestampMixin):
    """Maneuver plans for collision avoidance"""
    __tablename__ = 'maneuver_plans'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    collision_prediction_id = Column(UUID(as_uuid=True), ForeignKey('collision_predictions.id', ondelete='CASCADE'))
    satellite_id = Column(UUID(as_uuid=True), ForeignKey('satellites.id'), nullable=False, index=True)
    
    # Maneuver details
    maneuver_type = Column(String(30), nullable=False, index=True)
    execution_time = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Delta-V components (m/s)
    delta_v_radial = Column(Numeric(10, 6))
    delta_v_tangential = Column(Numeric(10, 6))
    delta_v_normal = Column(Numeric(10, 6))
    delta_v_total = Column(Numeric(10, 6), nullable=False)
    
    # Thrust vector (unit vector in ECI)
    thrust_direction_x = Column(Numeric(10, 8))
    thrust_direction_y = Column(Numeric(10, 8))
    thrust_direction_z = Column(Numeric(10, 8))
    
    # Execution parameters
    burn_duration_sec = Column(Numeric(8, 2))
    required_thrust_n = Column(Numeric(10, 4))
    fuel_consumption_kg = Column(Numeric(8, 3))
    
    # Success metrics
    success_probability = Column(Numeric(4, 3))
    risk_reduction_factor = Column(Numeric(4, 3))
    new_miss_distance_km = Column(Numeric(10, 6))
    
    # Implementation details
    complexity_level = Column(String(20), default='MODERATE')
    implementation_status = Column(String(20), default='PLANNED', index=True)
    approval_required = Column(Boolean, default=True)
    
    # Timing constraints
    decision_deadline = Column(DateTime(timezone=True))
    execution_window_start = Column(DateTime(timezone=True))
    execution_window_end = Column(DateTime(timezone=True))
    
    # Metadata
    created_by = Column(String(100))
    
    # Relationships
    collision_prediction = relationship("CollisionPrediction", back_populates="maneuver_plans")
    satellite = relationship("Satellite", back_populates="maneuver_plans")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "maneuver_type IN ('RADIAL_IN', 'RADIAL_OUT', 'TANGENTIAL_PROGRADE', 'TANGENTIAL_RETROGRADE', 'NORMAL_POSITIVE', 'NORMAL_NEGATIVE', 'COMBINED')",
            name='valid_maneuver_type'
        ),
        CheckConstraint(
            "complexity_level IN ('SIMPLE', 'MODERATE', 'COMPLEX', 'CRITICAL')",
            name='valid_complexity_level'
        ),
        CheckConstraint(
            "implementation_status IN ('PLANNED', 'APPROVED', 'SCHEDULED', 'EXECUTING', 'COMPLETED', 'FAILED', 'CANCELLED')",
            name='valid_implementation_status'
        ),
    )
    
    @property
    def delta_v_vector(self):
        """Delta-V as a tuple (radial, tangential, normal)"""
        return (
            float(self.delta_v_radial) if self.delta_v_radial else 0.0,
            float(self.delta_v_tangential) if self.delta_v_tangential else 0.0,
            float(self.delta_v_normal) if self.delta_v_normal else 0.0
        )
    
    @property
    def thrust_direction_vector(self):
        """Thrust direction as a unit vector tuple (x, y, z)"""
        if all(t is not None for t in [self.thrust_direction_x, self.thrust_direction_y, self.thrust_direction_z]):
            return (float(self.thrust_direction_x), float(self.thrust_direction_y), float(self.thrust_direction_z))
        return None
    
    def __repr__(self):
        return f"<ManeuverPlan(type='{self.maneuver_type}', delta_v={self.delta_v_total}m/s, status='{self.implementation_status}')>"

class SystemLog(Base):
    """System logs"""
    __tablename__ = 'system_logs'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    log_level = Column(String(10), nullable=False, index=True)
    component = Column(String(50), nullable=False, index=True)
    message = Column(Text, nullable=False)
    details = Column(JSONB)
    
    # Context
    object_type = Column(String(20), index=True)
    object_id = Column(UUID(as_uuid=True), index=True)
    user_session_id = Column(UUID(as_uuid=True))
    
    # Timing
    timestamp = Column(DateTime(timezone=True), default=func.now(), index=True)
    duration_ms = Column(Integer)
    
    # Classification
    category = Column(String(30), index=True)
    severity = Column(String(20), default='INFO')
    
    # Constraints
    __table_args__ = (
        CheckConstraint("log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')", name='valid_log_level'),
        CheckConstraint("severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')", name='valid_severity'),
        Index('idx_logs_object', 'object_type', 'object_id'),
    )
    
    def __repr__(self):
        return f"<SystemLog(level='{self.log_level}', component='{self.component}')>"

class UserSession(Base):
    """User sessions for tracking dashboard usage"""
    __tablename__ = 'user_sessions'
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    user_identifier = Column(String(100))
    
    # Session data
    start_time = Column(DateTime(timezone=True), default=func.now(), index=True)
    last_activity = Column(DateTime(timezone=True), default=func.now())
    end_time = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True, index=True)
    
    # Usage metrics
    page_views = Column(Integer, default=0)
    actions_performed = Column(Integer, default=0)
    data_queries = Column(Integer, default=0)
    
    # Client info
    user_agent = Column(Text)
    ip_address = Column(INET)
    browser_info = Column(JSONB)
    
    # Constraints
    __table_args__ = (
        CheckConstraint("end_time IS NULL OR end_time >= start_time", name='valid_session_duration'),
    )
    
    def __repr__(self):
        return f"<UserSession(token='{self.session_token[:8]}...', active={self.is_active})>"