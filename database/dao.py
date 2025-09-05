"""
Live Orbital Ballet - Data Access Objects (DAO)
High-level interface for database operations
"""

from datetime import datetime, timezone, timedelta
from typing import List, Optional, Dict, Tuple, Any
import logging
from decimal import Decimal
import uuid

from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from .connection import get_db_session
from .models import (
    TLEData, Satellite, DebrisObject, OrbitalState,
    RiskAssessment, CollisionPrediction, ManeuverPlan, SystemLog, UserSession
)

logger = logging.getLogger(__name__)

class TLEDataDAO:
    """Data Access Object for TLE data"""
    
    @staticmethod
    def create_or_update_tle(tle_data: dict) -> Optional[TLEData]:
        """Create or update TLE data"""
        try:
            with get_db_session() as session:
                # Check if TLE exists
                existing = session.query(TLEData).filter_by(norad_id=tle_data['norad_id']).first()
                
                if existing:
                    # Update existing TLE
                    for key, value in tle_data.items():
                        if hasattr(existing, key):
                            setattr(existing, key, value)
                    existing.updated_at = datetime.now(timezone.utc)
                    tle = existing
                else:
                    # Create new TLE
                    tle = TLEData(**tle_data)
                    session.add(tle)
                
                session.flush()
                return tle
                
        except Exception as e:
            logger.error(f"Error creating/updating TLE {tle_data.get('norad_id')}: {e}")
            return None
    
    @staticmethod
    def get_active_tles() -> List[TLEData]:
        """Get all active TLE data"""
        try:
            with get_db_session() as session:
                return session.query(TLEData).filter_by(is_active=True).all()
        except Exception as e:
            logger.error(f"Error fetching active TLEs: {e}")
            return []
    
    @staticmethod
    def get_tle_by_norad_id(norad_id: int) -> Optional[TLEData]:
        """Get TLE data by NORAD ID"""
        try:
            with get_db_session() as session:
                return session.query(TLEData).filter_by(norad_id=norad_id, is_active=True).first()
        except Exception as e:
            logger.error(f"Error fetching TLE for NORAD ID {norad_id}: {e}")
            return None
    
    @staticmethod
    def bulk_insert_tles(tle_list: List[dict]) -> int:
        """Bulk insert TLE data"""
        count = 0
        try:
            with get_db_session() as session:
                for tle_data in tle_list:
                    tle = TLEData(**tle_data)
                    session.add(tle)
                    count += 1
                
                session.flush()
                return count
                
        except Exception as e:
            logger.error(f"Error bulk inserting TLEs: {e}")
            return 0

class SatelliteDAO:
    """Data Access Object for satellites"""
    
    @staticmethod
    def create_satellite(satellite_data: dict) -> Optional[Satellite]:
        """Create a new satellite"""
        try:
            with get_db_session() as session:
                satellite = Satellite(**satellite_data)
                session.add(satellite)
                session.flush()
                return satellite
                
        except Exception as e:
            logger.error(f"Error creating satellite: {e}")
            return None
    
    @staticmethod
    def get_tracked_satellites() -> List[Satellite]:
        """Get all satellites being tracked"""
        try:
            with get_db_session() as session:
                return session.query(Satellite).filter_by(
                    operational_status='ACTIVE',
                    track_continuously=True
                ).order_by(desc(Satellite.priority_level)).all()
        except Exception as e:
            logger.error(f"Error fetching tracked satellites: {e}")
            return []
    
    @staticmethod
    def get_satellite_by_norad_id(norad_id: int) -> Optional[Satellite]:
        """Get satellite by NORAD ID"""
        try:
            with get_db_session() as session:
                return session.query(Satellite).filter_by(norad_id=norad_id).first()
        except Exception as e:
            logger.error(f"Error fetching satellite for NORAD ID {norad_id}: {e}")
            return None
    
    @staticmethod
    def update_tracking_status(satellite_id: uuid.UUID, last_tracked: datetime) -> bool:
        """Update satellite tracking status"""
        try:
            with get_db_session() as session:
                satellite = session.query(Satellite).filter_by(id=satellite_id).first()
                if satellite:
                    satellite.last_tracked = last_tracked
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating tracking status: {e}")
            return False

class OrbitalStateDAO:
    """Data Access Object for orbital states"""
    
    @staticmethod
    def save_orbital_state(state_data: dict) -> Optional[OrbitalState]:
        """Save orbital state"""
        try:
            with get_db_session() as session:
                state = OrbitalState(**state_data)
                session.add(state)
                session.flush()
                return state
                
        except Exception as e:
            logger.error(f"Error saving orbital state: {e}")
            return None
    
    @staticmethod
    def get_latest_state(object_type: str, object_id: uuid.UUID) -> Optional[OrbitalState]:
        """Get latest orbital state for an object"""
        try:
            with get_db_session() as session:
                return session.query(OrbitalState).filter_by(
                    object_type=object_type,
                    object_id=object_id
                ).order_by(desc(OrbitalState.epoch)).first()
        except Exception as e:
            logger.error(f"Error fetching latest state: {e}")
            return None
    
    @staticmethod
    def get_states_in_timerange(
        object_type: str, 
        object_id: uuid.UUID, 
        start_time: datetime, 
        end_time: datetime
    ) -> List[OrbitalState]:
        """Get orbital states in time range"""
        try:
            with get_db_session() as session:
                return session.query(OrbitalState).filter(
                    and_(
                        OrbitalState.object_type == object_type,
                        OrbitalState.object_id == object_id,
                        OrbitalState.epoch >= start_time,
                        OrbitalState.epoch <= end_time
                    )
                ).order_by(OrbitalState.epoch).all()
        except Exception as e:
            logger.error(f"Error fetching states in timerange: {e}")
            return []
    
    @staticmethod
    def get_current_positions(limit: int = 100) -> List[Dict[str, Any]]:
        """Get current positions for all tracked objects"""
        try:
            with get_db_session() as session:
                # Subquery to get latest state for each object
                subquery = session.query(
                    OrbitalState.object_type,
                    OrbitalState.object_id,
                    func.max(OrbitalState.epoch).label('max_epoch')
                ).group_by(
                    OrbitalState.object_type,
                    OrbitalState.object_id
                ).subquery()
                
                # Get the actual states
                states = session.query(OrbitalState).join(
                    subquery,
                    and_(
                        OrbitalState.object_type == subquery.c.object_type,
                        OrbitalState.object_id == subquery.c.object_id,
                        OrbitalState.epoch == subquery.c.max_epoch
                    )
                ).limit(limit).all()
                
                return [
                    {
                        'object_type': state.object_type,
                        'object_id': str(state.object_id),
                        'norad_id': state.norad_id,
                        'position': state.position_vector,
                        'velocity': state.velocity_vector,
                        'altitude_km': float(state.altitude_km) if state.altitude_km else None,
                        'epoch': state.epoch
                    }
                    for state in states
                ]
                
        except Exception as e:
            logger.error(f"Error fetching current positions: {e}")
            return []

class RiskAssessmentDAO:
    """Data Access Object for risk assessments"""
    
    @staticmethod
    def create_risk_assessment(assessment_data: dict) -> Optional[RiskAssessment]:
        """Create risk assessment"""
        try:
            with get_db_session() as session:
                assessment = RiskAssessment(**assessment_data)
                session.add(assessment)
                session.flush()
                return assessment
                
        except Exception as e:
            logger.error(f"Error creating risk assessment: {e}")
            return None
    
    @staticmethod
    def get_active_high_risk_assessments(threshold: float = 0.01) -> List[RiskAssessment]:
        """Get active high-risk assessments"""
        try:
            with get_db_session() as session:
                return session.query(RiskAssessment).filter(
                    and_(
                        RiskAssessment.is_active == True,
                        RiskAssessment.collision_probability >= threshold,
                        RiskAssessment.valid_until >= datetime.now(timezone.utc)
                    )
                ).order_by(desc(RiskAssessment.collision_probability)).all()
        except Exception as e:
            logger.error(f"Error fetching high-risk assessments: {e}")
            return []
    
    @staticmethod
    def get_assessments_for_object(
        object_type: str, 
        object_id: uuid.UUID, 
        active_only: bool = True
    ) -> List[RiskAssessment]:
        """Get risk assessments for a specific object"""
        try:
            with get_db_session() as session:
                query = session.query(RiskAssessment).filter(
                    or_(
                        and_(
                            RiskAssessment.primary_object_type == object_type,
                            RiskAssessment.primary_object_id == object_id
                        ),
                        and_(
                            RiskAssessment.secondary_object_type == object_type,
                            RiskAssessment.secondary_object_id == object_id
                        )
                    )
                )
                
                if active_only:
                    query = query.filter_by(is_active=True)
                
                return query.order_by(desc(RiskAssessment.collision_probability)).all()
                
        except Exception as e:
            logger.error(f"Error fetching assessments for object: {e}")
            return []

class CollisionPredictionDAO:
    """Data Access Object for collision predictions"""
    
    @staticmethod
    def create_collision_prediction(prediction_data: dict) -> Optional[CollisionPrediction]:
        """Create collision prediction"""
        try:
            with get_db_session() as session:
                prediction = CollisionPrediction(**prediction_data)
                session.add(prediction)
                session.flush()
                return prediction
                
        except Exception as e:
            logger.error(f"Error creating collision prediction: {e}")
            return None
    
    @staticmethod
    def get_active_predictions(time_horizon_hours: int = 72) -> List[CollisionPrediction]:
        """Get active collision predictions within time horizon"""
        try:
            with get_db_session() as session:
                cutoff_time = datetime.now(timezone.utc) + timedelta(hours=time_horizon_hours)
                
                return session.query(CollisionPrediction).filter(
                    and_(
                        CollisionPrediction.status == 'ACTIVE',
                        CollisionPrediction.predicted_collision_time <= cutoff_time,
                        CollisionPrediction.predicted_collision_time >= datetime.now(timezone.utc)
                    )
                ).order_by(CollisionPrediction.predicted_collision_time).all()
                
        except Exception as e:
            logger.error(f"Error fetching active predictions: {e}")
            return []
    
    @staticmethod
    def update_prediction_status(prediction_id: uuid.UUID, status: str) -> bool:
        """Update collision prediction status"""
        try:
            with get_db_session() as session:
                prediction = session.query(CollisionPrediction).filter_by(id=prediction_id).first()
                if prediction:
                    prediction.status = status
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating prediction status: {e}")
            return False

class ManeuverPlanDAO:
    """Data Access Object for maneuver plans"""
    
    @staticmethod
    def create_maneuver_plan(plan_data: dict) -> Optional[ManeuverPlan]:
        """Create maneuver plan"""
        try:
            with get_db_session() as session:
                plan = ManeuverPlan(**plan_data)
                session.add(plan)
                session.flush()
                return plan
                
        except Exception as e:
            logger.error(f"Error creating maneuver plan: {e}")
            return None
    
    @staticmethod
    def get_pending_maneuvers(satellite_id: Optional[uuid.UUID] = None) -> List[ManeuverPlan]:
        """Get pending maneuver plans"""
        try:
            with get_db_session() as session:
                query = session.query(ManeuverPlan).filter(
                    ManeuverPlan.implementation_status.in_(['PLANNED', 'APPROVED', 'SCHEDULED'])
                )
                
                if satellite_id:
                    query = query.filter_by(satellite_id=satellite_id)
                
                return query.order_by(ManeuverPlan.execution_time).all()
                
        except Exception as e:
            logger.error(f"Error fetching pending maneuvers: {e}")
            return []
    
    @staticmethod
    def update_maneuver_status(plan_id: uuid.UUID, status: str) -> bool:
        """Update maneuver plan status"""
        try:
            with get_db_session() as session:
                plan = session.query(ManeuverPlan).filter_by(id=plan_id).first()
                if plan:
                    plan.implementation_status = status
                    return True
                return False
        except Exception as e:
            logger.error(f"Error updating maneuver status: {e}")
            return False

class SystemLogDAO:
    """Data Access Object for system logs"""
    
    @staticmethod
    def log_event(
        level: str,
        component: str,
        message: str,
        details: Optional[dict] = None,
        object_type: Optional[str] = None,
        object_id: Optional[uuid.UUID] = None,
        category: Optional[str] = None,
        severity: str = 'INFO'
    ) -> bool:
        """Log system event"""
        try:
            with get_db_session() as session:
                log_entry = SystemLog(
                    log_level=level,
                    component=component,
                    message=message,
                    details=details,
                    object_type=object_type,
                    object_id=object_id,
                    category=category,
                    severity=severity
                )
                session.add(log_entry)
                return True
                
        except Exception as e:
            logger.error(f"Error logging event: {e}")
            return False
    
    @staticmethod
    def get_recent_logs(
        hours: int = 24,
        level: Optional[str] = None,
        component: Optional[str] = None,
        limit: int = 1000
    ) -> List[SystemLog]:
        """Get recent log entries"""
        try:
            with get_db_session() as session:
                cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
                
                query = session.query(SystemLog).filter(
                    SystemLog.timestamp >= cutoff_time
                )
                
                if level:
                    query = query.filter_by(log_level=level)
                
                if component:
                    query = query.filter_by(component=component)
                
                return query.order_by(desc(SystemLog.timestamp)).limit(limit).all()
                
        except Exception as e:
            logger.error(f"Error fetching recent logs: {e}")
            return []

class AnalyticsDAO:
    """Data Access Object for analytics and reporting"""
    
    @staticmethod
    def get_system_statistics() -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        stats = {}
        try:
            with get_db_session() as session:
                # Object counts
                stats['satellites_active'] = session.query(Satellite).filter_by(
                    operational_status='ACTIVE'
                ).count()
                
                stats['satellites_total'] = session.query(Satellite).count()
                stats['debris_objects'] = session.query(DebrisObject).count()
                stats['tle_records'] = session.query(TLEData).filter_by(is_active=True).count()
                
                # Risk assessments
                stats['high_risk_events'] = session.query(RiskAssessment).filter(
                    and_(
                        RiskAssessment.is_active == True,
                        RiskAssessment.collision_probability >= 0.01
                    )
                ).count()
                
                # Active predictions
                stats['active_predictions'] = session.query(CollisionPrediction).filter_by(
                    status='ACTIVE'
                ).count()
                
                # Pending maneuvers
                stats['pending_maneuvers'] = session.query(ManeuverPlan).filter(
                    ManeuverPlan.implementation_status.in_(['PLANNED', 'APPROVED', 'SCHEDULED'])
                ).count()
                
                # Recent activity (last 24 hours)
                recent_time = datetime.now(timezone.utc) - timedelta(hours=24)
                
                stats['recent_risk_assessments'] = session.query(RiskAssessment).filter(
                    RiskAssessment.created_at >= recent_time
                ).count()
                
                stats['recent_orbital_states'] = session.query(OrbitalState).filter(
                    OrbitalState.computed_at >= recent_time
                ).count()
                
                # Error counts
                stats['recent_errors'] = session.query(SystemLog).filter(
                    and_(
                        SystemLog.timestamp >= recent_time,
                        SystemLog.log_level.in_(['ERROR', 'CRITICAL'])
                    )
                ).count()
                
        except Exception as e:
            logger.error(f"Error computing system statistics: {e}")
        
        return stats
    
    @staticmethod
    def get_collision_risk_trends(days: int = 7) -> List[Dict[str, Any]]:
        """Get collision risk trends over time"""
        try:
            with get_db_session() as session:
                start_time = datetime.now(timezone.utc) - timedelta(days=days)
                
                # Group assessments by day and risk category
                trends = session.query(
                    func.date_trunc('day', RiskAssessment.created_at).label('date'),
                    RiskAssessment.risk_category,
                    func.count(RiskAssessment.id).label('count'),
                    func.avg(RiskAssessment.collision_probability).label('avg_probability')
                ).filter(
                    RiskAssessment.created_at >= start_time
                ).group_by(
                    func.date_trunc('day', RiskAssessment.created_at),
                    RiskAssessment.risk_category
                ).order_by('date').all()
                
                return [
                    {
                        'date': trend.date.isoformat(),
                        'risk_category': trend.risk_category,
                        'count': trend.count,
                        'avg_probability': float(trend.avg_probability) if trend.avg_probability else 0.0
                    }
                    for trend in trends
                ]
                
        except Exception as e:
            logger.error(f"Error computing collision risk trends: {e}")
            return []

# Convenience functions for common operations
def log_info(component: str, message: str, **kwargs):
    """Log info message"""
    SystemLogDAO.log_event('INFO', component, message, **kwargs)

def log_warning(component: str, message: str, **kwargs):
    """Log warning message"""
    SystemLogDAO.log_event('WARNING', component, message, severity='MEDIUM', **kwargs)

def log_error(component: str, message: str, **kwargs):
    """Log error message"""
    SystemLogDAO.log_event('ERROR', component, message, severity='HIGH', **kwargs)

def log_critical(component: str, message: str, **kwargs):
    """Log critical message"""
    SystemLogDAO.log_event('CRITICAL', component, message, severity='CRITICAL', **kwargs)