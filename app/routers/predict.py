# app/routers/predict.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Encounter
from app.services.ml_predictor import predictor
from pydantic import BaseModel

router = APIRouter(prefix="/predict", tags=["Predictions"])

class ReadmissionPrediction(BaseModel):
    encounter_id: int
    risk_score: float
    risk_level: str
    risk_factors: list

@router.get("/readmission/{encounter_id}", response_model=ReadmissionPrediction)
def predict_readmission(encounter_id: int, db: Session = Depends(get_db)):
    """
    Predict 30-day readmission risk using XGBoost + SHAP explanations
    """
    # Fetch encounter
    encounter = db.query(Encounter).filter(Encounter.encounter_id == encounter_id).first()
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found")
    
    # Prepare feature dict (15 features in correct order)
    features = {
        "age_years_cleaned": encounter.age_years_cleaned,
        "gender_M": encounter.gender_M,
        "los_days": encounter.los_days,
        "previous_admissions": encounter.previous_admissions,
        "days_since_last_admit": encounter.days_since_last_admit,
        "diagnosis_count": encounter.diagnosis_count,
        "charlson_score": encounter.charlson_score,
        "procedure_count": encounter.procedure_count,
        "icu_stay_count": encounter.icu_stay_count,
        "icu_los_days": encounter.icu_los_days,
        "admit_type_EMERGENCY": encounter.admit_type_EMERGENCY,
        "admit_type_URGENT": encounter.admit_type_URGENT,
        "insurance_Medicare": encounter.insurance_Medicare,
        "insurance_Private": encounter.insurance_Private,
        "hospital_expire_flag": encounter.hospital_expire_flag
    }
    
    # Predict with XGBoost
    prediction = predictor.predict(features)
    
    # Update encounter risk in DB
    encounter.risk_score = prediction["risk_score"]
    encounter.risk_level = prediction["risk_level"]
    db.commit()
    
    return {
        "encounter_id": encounter_id,
        **prediction
    }

@router.post("/batch/recompute")
def recompute_all_risks(db: Session = Depends(get_db)):
    """
    Recompute risk scores for all encounters (run after model update)
    """
    encounters = db.query(Encounter).all()
    updated = 0
    
    for encounter in encounters:
        features = {
            "age_years_cleaned": encounter.age_years_cleaned,
            "gender_M": encounter.gender_M,
            "los_days": encounter.los_days,
            "previous_admissions": encounter.previous_admissions,
            "days_since_last_admit": encounter.days_since_last_admit,
            "diagnosis_count": encounter.diagnosis_count,
            "charlson_score": encounter.charlson_score,
            "procedure_count": encounter.procedure_count,
            "icu_stay_count": encounter.icu_stay_count,
            "icu_los_days": encounter.icu_los_days,
            "admit_type_EMERGENCY": encounter.admit_type_EMERGENCY,
            "admit_type_URGENT": encounter.admit_type_URGENT,
            "insurance_Medicare": encounter.insurance_Medicare,
            "insurance_Private": encounter.insurance_Private,
            "hospital_expire_flag": encounter.hospital_expire_flag
        }
        
        prediction = predictor.predict(features)
        encounter.risk_score = prediction["risk_score"]
        encounter.risk_level = prediction["risk_level"]
        updated += 1
    
    db.commit()
    return {"status": "success", "updated_encounters": updated}
