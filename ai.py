"""
Live Orbital Ballet - AI Risk Assessment Module
Hybrid risk scoring using rule-based physics + PyTorch ML model for collision detection
"""

import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass
import logging
from sklearn.preprocessing import StandardScaler, MinMaxScaler
import joblib
import os
from scipy.spatial.distance import euclidean
import math

logger = logging.getLogger(__name__)

@dataclass
class RiskFeatures:
    """Feature vector for collision risk assessment"""
    # Geometric features
    distance_km: float
    relative_velocity_kms: float  
    approach_angle_deg: float
    
    # Orbital features
    altitude_diff_km: float
    inclination_diff_deg: float
    eccentricity_product: float
    
    # Temporal features  
    time_to_closest_approach_hours: float
    prediction_uncertainty: float
    
    # Object characteristics
    object1_size_factor: float
    object2_size_factor: float
    combined_mass_factor: float
    
    # Environmental factors
    atmospheric_density_factor: float
    solar_activity_factor: float
    
    def to_tensor(self) -> torch.Tensor:
        """Convert features to PyTorch tensor"""
        features = [
            self.distance_km,
            self.relative_velocity_kms,
            self.approach_angle_deg,
            self.altitude_diff_km,
            self.inclination_diff_deg,
            self.eccentricity_product,
            self.time_to_closest_approach_hours,
            self.prediction_uncertainty,
            self.object1_size_factor,
            self.object2_size_factor,
            self.combined_mass_factor,
            self.atmospheric_density_factor,
            self.solar_activity_factor
        ]
        return torch.tensor(features, dtype=torch.float32)
    
    def to_array(self) -> np.ndarray:
        """Convert features to numpy array"""
        return self.to_tensor().numpy()

class CollisionRiskNN(nn.Module):
    """
    Neural Network for collision risk assessment
    Architecture: Multi-layer perceptron with residual connections
    """
    
    def __init__(self, input_dim: int = 13, hidden_dims: List[int] = [64, 32, 16], 
                 dropout_rate: float = 0.2):
        super(CollisionRiskNN, self).__init__()
        
        self.input_dim = input_dim
        self.hidden_dims = hidden_dims
        self.dropout_rate = dropout_rate
        
        # Input layer with batch normalization
        self.input_layer = nn.Sequential(
            nn.Linear(input_dim, hidden_dims[0]),
            nn.BatchNorm1d(hidden_dims[0]),
            nn.ReLU(),
            nn.Dropout(dropout_rate)
        )
        
        # Hidden layers with residual connections
        self.hidden_layers = nn.ModuleList()
        for i in range(len(hidden_dims) - 1):
            layer = nn.Sequential(
                nn.Linear(hidden_dims[i], hidden_dims[i + 1]),
                nn.BatchNorm1d(hidden_dims[i + 1]),
                nn.ReLU(),
                nn.Dropout(dropout_rate)
            )
            self.hidden_layers.append(layer)
        
        # Output layer (probability of collision)
        self.output_layer = nn.Sequential(
            nn.Linear(hidden_dims[-1], 1),
            nn.Sigmoid()  # Output between 0 and 1
        )
        
        # Initialize weights
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialize network weights using Xavier initialization"""
        for module in self.modules():
            if isinstance(module, nn.Linear):
                nn.init.xavier_uniform_(module.weight)
                nn.init.constant_(module.bias, 0)
    
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """Forward pass through the network"""
        # Handle single sample input
        if x.dim() == 1:
            x = x.unsqueeze(0)
        
        # Input layer
        x = self.input_layer(x)
        
        # Hidden layers with residual connections
        for i, layer in enumerate(self.hidden_layers):
            residual = x
            x = layer(x)
            
            # Add residual connection if dimensions match
            if residual.size(-1) == x.size(-1):
                x = x + residual
        
        # Output layer
        risk_probability = self.output_layer(x)
        
        return risk_probability.squeeze()
    
    def predict_risk(self, features: Union[RiskFeatures, torch.Tensor, np.ndarray]) -> float:
        """Predict collision risk from features"""
        self.eval()
        
        with torch.no_grad():
            if isinstance(features, RiskFeatures):
                x = features.to_tensor()
            elif isinstance(features, np.ndarray):
                x = torch.tensor(features, dtype=torch.float32)
            else:
                x = features
            
            risk_prob = self.forward(x)
            return float(risk_prob.item())

class PhysicsBasedRiskAnalyzer:
    """
    Rule-based risk analyzer using orbital mechanics principles
    """
    
    def __init__(self):
        self.earth_radius = 6371.0  # km
        self.earth_mu = 398600.4418  # km³/s²
        
    def calculate_physics_risk(self, features: RiskFeatures) -> Dict[str, float]:
        """
        Calculate collision risk using physics-based rules
        
        Returns:
            Dictionary with individual risk components and overall score
        """
        risk_components = {}
        
        # 1. Distance-based risk (primary factor)
        risk_components['distance_risk'] = self._calculate_distance_risk(features.distance_km)
        
        # 2. Velocity-based risk
        risk_components['velocity_risk'] = self._calculate_velocity_risk(features.relative_velocity_kms)
        
        # 3. Approach geometry risk
        risk_components['geometry_risk'] = self._calculate_geometry_risk(features.approach_angle_deg)
        
        # 4. Time-based risk (urgency)
        risk_components['temporal_risk'] = self._calculate_temporal_risk(
            features.time_to_closest_approach_hours
        )
        
        # 5. Orbital similarity risk
        risk_components['orbital_risk'] = self._calculate_orbital_similarity_risk(
            features.altitude_diff_km, features.inclination_diff_deg
        )
        
        # 6. Size-based risk (collision cross-section)
        risk_components['size_risk'] = self._calculate_size_risk(
            features.object1_size_factor, features.object2_size_factor
        )
        
        # 7. Uncertainty risk
        risk_components['uncertainty_risk'] = self._calculate_uncertainty_risk(
            features.prediction_uncertainty
        )
        
        # Calculate weighted overall risk
        weights = {
            'distance_risk': 0.35,
            'velocity_risk': 0.20,
            'geometry_risk': 0.15,
            'temporal_risk': 0.10,
            'orbital_risk': 0.10,
            'size_risk': 0.05,
            'uncertainty_risk': 0.05
        }
        
        overall_risk = sum(
            risk_components[component] * weights[component]
            for component in weights
        )
        
        risk_components['overall_physics_risk'] = min(overall_risk, 1.0)
        
        return risk_components
    
    def _calculate_distance_risk(self, distance_km: float) -> float:
        """Risk increases exponentially as distance decreases"""
        if distance_km <= 0.001:  # 1 meter
            return 1.0
        
        # Risk peaks at collision radius, decays exponentially
        collision_radius = 0.01  # 10 meters in km
        if distance_km <= collision_radius:
            return 1.0 - (distance_km / collision_radius) * 0.1
        
        # Exponential decay beyond collision radius
        risk = np.exp(-(distance_km - collision_radius) / 0.5)
        return min(risk, 1.0)
    
    def _calculate_velocity_risk(self, rel_velocity_kms: float) -> float:
        """Higher relative velocity = less time to react, higher risk"""
        # Risk increases with relative velocity up to a point
        # Very high velocities actually reduce collision probability 
        # (less time in collision zone)
        
        if rel_velocity_kms < 0.5:  # Very slow relative motion
            return 0.1
        
        if rel_velocity_kms < 5.0:  # Normal orbital velocities
            return rel_velocity_kms / 5.0
        
        if rel_velocity_kms < 15.0:  # High velocity
            return 0.8 + (rel_velocity_kms - 5.0) / 50.0
        
        # Extremely high velocity - less collision time
        return max(0.9 - (rel_velocity_kms - 15.0) / 100.0, 0.3)
    
    def _calculate_geometry_risk(self, approach_angle_deg: float) -> float:
        """Head-on approaches are riskier than glancing approaches"""
        # Convert angle to risk (0° = head-on = highest risk)
        angle_rad = np.radians(approach_angle_deg)
        
        # Risk peaks at 0° (head-on) and 180° (head-on from behind)
        # Minimum at 90° (perpendicular)
        risk = 1.0 - abs(np.sin(angle_rad))
        return max(risk, 0.1)
    
    def _calculate_temporal_risk(self, time_to_approach_hours: float) -> float:
        """Urgency increases as approach time decreases"""
        if time_to_approach_hours <= 0:
            return 1.0
        
        if time_to_approach_hours < 1:  # Less than 1 hour
            return 1.0 - time_to_approach_hours * 0.2
        
        if time_to_approach_hours < 24:  # Less than 1 day
            return 0.8 - (time_to_approach_hours - 1) / 30.0
        
        # Longer term approaches have lower urgency
        return max(0.5 - (time_to_approach_hours - 24) / 200.0, 0.1)
    
    def _calculate_orbital_similarity_risk(self, altitude_diff_km: float, 
                                        inclination_diff_deg: float) -> float:
        """Objects in similar orbits have higher long-term collision risk"""
        # Normalize differences
        altitude_similarity = 1.0 - min(abs(altitude_diff_km) / 1000.0, 1.0)
        inclination_similarity = 1.0 - min(abs(inclination_diff_deg) / 180.0, 1.0)
        
        # Combined similarity score
        similarity = (altitude_similarity + inclination_similarity) / 2.0
        
        # Higher similarity = higher long-term risk
        return similarity * 0.5  # Scale down as this is secondary factor
    
    def _calculate_size_risk(self, size1_factor: float, size2_factor: float) -> float:
        """Larger objects have higher collision cross-sections"""
        combined_size = (size1_factor + size2_factor) / 2.0
        return min(combined_size, 1.0)
    
    def _calculate_uncertainty_risk(self, uncertainty: float) -> float:
        """Higher prediction uncertainty increases risk assessment"""
        return min(uncertainty, 1.0)

class HybridRiskAssessment:
    """
    Combines physics-based rules with ML model for comprehensive risk assessment
    """
    
    def __init__(self, model_path: Optional[str] = None, use_pretrained: bool = True):
        self.physics_analyzer = PhysicsBasedRiskAnalyzer()
        self.ml_model = CollisionRiskNN()
        self.feature_scaler = StandardScaler()
        self.is_trained = False
        self.model_path = model_path or "collision_risk_model.pth"
        
        # Initialize with synthetic training if enabled
        if use_pretrained:
            self._initialize_with_synthetic_training()
    
    def _initialize_with_synthetic_training(self):
        """Initialize model with synthetic training data"""
        logger.info("Initializing ML model with synthetic training data...")
        
        # Generate synthetic training data
        training_features, training_labels = self._generate_synthetic_training_data(1000)
        
        # Train the model
        self._train_model(training_features, training_labels)
        
        logger.info("ML model initialized successfully")
    
    def _generate_synthetic_training_data(self, num_samples: int) -> Tuple[List[RiskFeatures], List[float]]:
        """Generate synthetic training data for the ML model"""
        features = []
        labels = []
        
        for _ in range(num_samples):
            # Generate random feature values with realistic distributions
            distance = np.random.exponential(5.0)  # Exponential distribution favoring close approaches
            rel_velocity = np.random.gamma(2, 2)   # Gamma distribution for velocities
            approach_angle = np.random.uniform(0, 180)
            altitude_diff = np.random.normal(0, 500)
            inclination_diff = np.random.uniform(0, 180)
            eccentricity_product = np.random.beta(2, 5)  # Most orbits are nearly circular
            time_to_approach = np.random.exponential(24)  # Hours
            uncertainty = np.random.beta(1, 4)  # Low uncertainty preferred
            size1 = np.random.lognormal(0, 1)
            size2 = np.random.lognormal(0, 1)
            mass_factor = (size1 + size2) / 2
            atmos_factor = np.random.beta(2, 3)
            solar_factor = np.random.beta(2, 3)
            
            feature = RiskFeatures(
                distance_km=distance,
                relative_velocity_kms=rel_velocity,
                approach_angle_deg=approach_angle,
                altitude_diff_km=altitude_diff,
                inclination_diff_deg=inclination_diff,
                eccentricity_product=eccentricity_product,
                time_to_closest_approach_hours=time_to_approach,
                prediction_uncertainty=uncertainty,
                object1_size_factor=size1,
                object2_size_factor=size2,
                combined_mass_factor=mass_factor,
                atmospheric_density_factor=atmos_factor,
                solar_activity_factor=solar_factor
            )
            
            # Calculate ground truth using enhanced physics model
            physics_risk = self.physics_analyzer.calculate_physics_risk(feature)
            
            # Add some noise and nonlinearity to create realistic training data
            base_risk = physics_risk['overall_physics_risk']
            
            # Add interaction effects
            interaction_effects = 0
            if distance < 1.0 and rel_velocity > 10:  # High speed close approach
                interaction_effects += 0.2
            if abs(altitude_diff) < 50 and abs(inclination_diff) < 5:  # Similar orbits
                interaction_effects += 0.1
            
            label = min(base_risk + interaction_effects + np.random.normal(0, 0.05), 1.0)
            label = max(label, 0.0)
            
            features.append(feature)
            labels.append(label)
        
        return features, labels
    
    def _train_model(self, features: List[RiskFeatures], labels: List[float]):
        """Train the ML model on provided data"""
        # Convert features to arrays
        feature_arrays = [f.to_array() for f in features]
        X = np.array(feature_arrays)
        y = np.array(labels)
        
        # Fit scaler
        self.feature_scaler.fit(X)
        X_scaled = self.feature_scaler.transform(X)
        
        # Convert to tensors
        X_tensor = torch.tensor(X_scaled, dtype=torch.float32)
        y_tensor = torch.tensor(y, dtype=torch.float32)
        
        # Training setup
        self.ml_model.train()
        optimizer = torch.optim.Adam(self.ml_model.parameters(), lr=0.001, weight_decay=1e-4)
        criterion = nn.MSELoss()
        
        # Training loop
        batch_size = 32
        num_epochs = 100
        
        for epoch in range(num_epochs):
            total_loss = 0
            num_batches = len(X_tensor) // batch_size
            
            for i in range(0, len(X_tensor), batch_size):
                batch_X = X_tensor[i:i + batch_size]
                batch_y = y_tensor[i:i + batch_size]
                
                optimizer.zero_grad()
                outputs = self.ml_model(batch_X)
                loss = criterion(outputs, batch_y)
                loss.backward()
                optimizer.step()
                
                total_loss += loss.item()
            
            if epoch % 20 == 0:
                avg_loss = total_loss / num_batches
                logger.debug(f"Epoch {epoch}, Average Loss: {avg_loss:.6f}")
        
        self.is_trained = True
        logger.info("ML model training completed")
    
    def assess_collision_risk(self, features: RiskFeatures, 
                            physics_weight: float = 0.4,
                            ml_weight: float = 0.6) -> Dict[str, float]:
        """
        Comprehensive collision risk assessment using hybrid approach
        
        Args:
            features: Risk assessment features
            physics_weight: Weight for physics-based assessment (0-1)
            ml_weight: Weight for ML-based assessment (0-1)
            
        Returns:
            Dictionary with detailed risk assessment
        """
        # Ensure weights sum to 1
        total_weight = physics_weight + ml_weight
        physics_weight /= total_weight
        ml_weight /= total_weight
        
        # Physics-based assessment
        physics_results = self.physics_analyzer.calculate_physics_risk(features)
        physics_risk = physics_results['overall_physics_risk']
        
        # ML-based assessment
        ml_risk = 0.0
        if self.is_trained:
            # Scale features for ML model
            feature_array = features.to_array().reshape(1, -1)
            scaled_features = self.feature_scaler.transform(feature_array)
            scaled_tensor = torch.tensor(scaled_features[0], dtype=torch.float32)
            
            ml_risk = self.ml_model.predict_risk(scaled_tensor)
        else:
            logger.warning("ML model not trained, using physics-only assessment")
            ml_weight = 0.0
            physics_weight = 1.0
        
        # Combine assessments
        hybrid_risk = physics_weight * physics_risk + ml_weight * ml_risk
        
        # Confidence calculation based on agreement between methods
        agreement = 1.0 - abs(physics_risk - ml_risk)
        confidence = agreement * 0.8 + 0.2  # Minimum 20% confidence
        
        # Risk categorization
        risk_category = self._categorize_risk_level(hybrid_risk)
        
        return {
            'hybrid_risk_score': hybrid_risk,
            'physics_risk_score': physics_risk,
            'ml_risk_score': ml_risk,
            'confidence': confidence,
            'risk_category': risk_category,
            'physics_components': physics_results,
            'assessment_timestamp': datetime.utcnow(),
            'weights_used': {
                'physics': physics_weight,
                'ml': ml_weight
            }
        }
    
    def _categorize_risk_level(self, risk_score: float) -> str:
        """Categorize numerical risk score into descriptive levels"""
        if risk_score >= 0.8:
            return 'CRITICAL'
        elif risk_score >= 0.6:
            return 'HIGH'
        elif risk_score >= 0.4:
            return 'MEDIUM'
        elif risk_score >= 0.2:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def batch_assess_risks(self, feature_list: List[RiskFeatures]) -> List[Dict]:
        """Assess collision risks for multiple scenarios"""
        results = []
        
        for features in feature_list:
            risk_assessment = self.assess_collision_risk(features)
            results.append(risk_assessment)
        
        return results
    
    def save_model(self, path: Optional[str] = None):
        """Save the trained ML model and scaler"""
        save_path = path or self.model_path
        
        if self.is_trained:
            model_data = {
                'model_state_dict': self.ml_model.state_dict(),
                'scaler': self.feature_scaler,
                'model_config': {
                    'input_dim': self.ml_model.input_dim,
                    'hidden_dims': self.ml_model.hidden_dims,
                    'dropout_rate': self.ml_model.dropout_rate
                },
                'training_timestamp': datetime.utcnow()
            }
            
            torch.save(model_data, save_path)
            logger.info(f"Model saved to {save_path}")
        else:
            logger.warning("Cannot save untrained model")
    
    def load_model(self, path: Optional[str] = None):
        """Load a pre-trained ML model and scaler"""
        load_path = path or self.model_path
        
        if os.path.exists(load_path):
            try:
                model_data = torch.load(load_path, map_location='cpu')
                
                # Recreate model with saved configuration
                config = model_data['model_config']
                self.ml_model = CollisionRiskNN(
                    input_dim=config['input_dim'],
                    hidden_dims=config['hidden_dims'],
                    dropout_rate=config['dropout_rate']
                )
                
                # Load state dict and scaler
                self.ml_model.load_state_dict(model_data['model_state_dict'])
                self.feature_scaler = model_data['scaler']
                self.is_trained = True
                
                logger.info(f"Model loaded from {load_path}")
                
            except Exception as e:
                logger.error(f"Failed to load model: {e}")
                self._initialize_with_synthetic_training()
        else:
            logger.warning(f"Model file not found: {load_path}")
            self._initialize_with_synthetic_training()

# Utility functions for feature extraction
def extract_risk_features(orbital_state1, orbital_state2, debris_data=None) -> RiskFeatures:
    """
    Extract risk assessment features from orbital states and debris data
    
    Args:
        orbital_state1: First object's orbital state
        orbital_state2: Second object's orbital state  
        debris_data: Additional debris information (optional)
        
    Returns:
        RiskFeatures object
    """
    # Calculate basic geometric features
    pos1 = np.array(orbital_state1.position)
    pos2 = np.array(orbital_state2.position)
    vel1 = np.array(orbital_state1.velocity)
    vel2 = np.array(orbital_state2.velocity)
    
    distance = euclidean(pos1, pos2)
    relative_velocity_vec = vel1 - vel2
    relative_velocity = np.linalg.norm(relative_velocity_vec)
    
    # Calculate approach angle
    position_diff = pos2 - pos1
    if np.linalg.norm(position_diff) > 0:
        approach_angle = np.arccos(
            np.clip(np.dot(relative_velocity_vec, position_diff) / 
                   (np.linalg.norm(relative_velocity_vec) * np.linalg.norm(position_diff)), 
                   -1, 1)
        )
        approach_angle_deg = np.degrees(approach_angle)
    else:
        approach_angle_deg = 0.0
    
    # Calculate altitude difference
    earth_radius = 6371.0
    alt1 = np.linalg.norm(pos1) - earth_radius
    alt2 = np.linalg.norm(pos2) - earth_radius
    altitude_diff = abs(alt1 - alt2)
    
    # Default values for missing orbital elements
    inclination_diff = 5.0  # Default reasonable value
    eccentricity_product = 0.01  # Assume circular orbits
    
    # Time-based features (simplified)
    time_to_approach = 1.0  # Assume 1 hour for current approach
    uncertainty = 0.1  # 10% uncertainty
    
    # Size factors (use defaults if debris data not available)
    if debris_data:
        size1 = getattr(debris_data, 'size', 1.0) / 10.0  # Normalize to 0-1
        size2 = 1.0  # Assume standard satellite size
        mass_factor = (size1 + size2) / 2
    else:
        size1 = size2 = mass_factor = 0.5  # Default medium size
    
    # Environmental factors (simplified)
    atmos_factor = max(0.1, 1.0 - alt1 / 1000.0)  # Higher at lower altitudes
    solar_factor = 0.5  # Neutral solar activity
    
    return RiskFeatures(
        distance_km=distance,
        relative_velocity_kms=relative_velocity,
        approach_angle_deg=approach_angle_deg,
        altitude_diff_km=altitude_diff,
        inclination_diff_deg=inclination_diff,
        eccentricity_product=eccentricity_product,
        time_to_closest_approach_hours=time_to_approach,
        prediction_uncertainty=uncertainty,
        object1_size_factor=size1,
        object2_size_factor=size2,
        combined_mass_factor=mass_factor,
        atmospheric_density_factor=atmos_factor,
        solar_activity_factor=solar_factor
    )

# Example usage and testing
if __name__ == "__main__":
    # Initialize hybrid risk assessment
    risk_assessor = HybridRiskAssessment()
    
    # Test with sample features
    test_features = RiskFeatures(
        distance_km=0.5,
        relative_velocity_kms=12.0,
        approach_angle_deg=15.0,
        altitude_diff_km=50.0,
        inclination_diff_deg=2.0,
        eccentricity_product=0.02,
        time_to_closest_approach_hours=2.0,
        prediction_uncertainty=0.15,
        object1_size_factor=0.8,
        object2_size_factor=0.3,
        combined_mass_factor=0.55,
        atmospheric_density_factor=0.3,
        solar_activity_factor=0.6
    )
    
    # Perform risk assessment
    risk_result = risk_assessor.assess_collision_risk(test_features)
    
    print(f"Hybrid Risk Assessment Results:")
    print(f"Overall Risk Score: {risk_result['hybrid_risk_score']:.4f}")
    print(f"Risk Category: {risk_result['risk_category']}")
    print(f"Confidence: {risk_result['confidence']:.3f}")
    print(f"Physics Risk: {risk_result['physics_risk_score']:.4f}")
    print(f"ML Risk: {risk_result['ml_risk_score']:.4f}")
    
    # Save the trained model
    risk_assessor.save_model()
    print("Model saved successfully")