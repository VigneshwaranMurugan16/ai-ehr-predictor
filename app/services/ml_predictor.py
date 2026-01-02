# app/services/ml_predictor.py
import pickle
import numpy as np
import os
from pathlib import Path

class ReadmissionPredictor:
    def __init__(self):
        self.model_dir = Path.home() / "ai-ehr-predictor" / "models"
        self.model = None
        self.explainer = None
        self.feature_names = None
        self._load_model()
    
    def _load_model(self):
        """Load trained XGBoost model and SHAP explainer"""
        try:
            with open(self.model_dir / "xgboost_readmission.pkl", "rb") as f:
                self.model = pickle.load(f)
            
            with open(self.model_dir / "shap_explainer.pkl", "rb") as f:
                self.explainer = pickle.load(f)
            
            import json
            with open(self.model_dir / "feature_names.json", "r") as f:
                self.feature_names = json.load(f)
            
            print(f"✅ Loaded XGBoost model with {len(self.feature_names)} features")
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            raise
    
    def predict(self, encounter_features: dict) -> dict:
        """
        Predict readmission risk with SHAP explanations
        
        Args:
            encounter_features: Dict with 15 feature values
        
        Returns:
            {
                "risk_score": float (0-1),
                "risk_level": str ("low", "medium", "high"),
                "risk_factors": [{"feature": str, "impact": float, "value": float}]
            }
        """
        # Extract features in correct order
        feature_vector = [encounter_features[feat] for feat in self.feature_names]
        feature_array = np.array(feature_vector).reshape(1, -1)
        
        # Predict probability
        risk_prob = self.model.predict_proba(feature_array)[0][1]
        
        # Determine risk level
        if risk_prob >= 0.15:
            risk_level = "high"
        elif risk_prob >= 0.08:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        # Calculate SHAP values for explanation
        shap_values = self.explainer.shap_values(feature_array)[0]
        
        # Get top 5 risk factors
        shap_importance = [(self.feature_names[i], shap_values[i], feature_vector[i]) 
                          for i in range(len(shap_values))]
        shap_importance.sort(key=lambda x: abs(x[1]), reverse=True)
        
        risk_factors = [
            {
                "feature": self._format_feature_name(feat),
                "impact": float(impact),
                "value": float(val),
                "direction": "increases" if impact > 0 else "decreases"
            }
            for feat, impact, val in shap_importance[:5]
        ]
        
        return {
            "risk_score": float(risk_prob),
            "risk_level": risk_level,
            "risk_factors": risk_factors
        }
    
    def _format_feature_name(self, feature: str) -> str:
        """Convert feature name to human-readable format"""
        name_map = {
            "age_years_cleaned": "Age",
            "gender_M": "Gender (Male)",
            "los_days": "Hospital Length of Stay",
            "previous_admissions": "Previous Admissions",
            "days_since_last_admit": "Days Since Last Admission",
            "diagnosis_count": "Number of Diagnoses",
            "charlson_score": "Charlson Comorbidity Score",
            "procedure_count": "Number of Procedures",
            "icu_stay_count": "ICU Stays",
            "icu_los_days": "ICU Length of Stay",
            "admit_type_EMERGENCY": "Emergency Admission",
            "admit_type_URGENT": "Urgent Admission",
            "insurance_Medicare": "Medicare Insurance",
            "insurance_Private": "Private Insurance",
            "hospital_expire_flag": "In-Hospital Mortality"
        }
        return name_map.get(feature, feature)

# Global instance (singleton)
predictor = ReadmissionPredictor()
