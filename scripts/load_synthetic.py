# scripts/load_synthetic.py
# scripts/load_synthetic.py
import csv
from datetime import datetime, date
from sqlalchemy.orm import Session

from app.db import Base, engine, SessionLocal  # ← Change this line
from app.models import Patient, Encounter, Task


def parse_date(value: str) -> date | None:
    """Parse YYYY-MM-DD string to date object"""
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None

def load_patients(session: Session, path: str) -> None:
    """Load patients from CSV"""
    print(f"Loading patients from {path}...")
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        print(f"Read {len(rows)} patient rows")
        
        for row in rows:
            patient = Patient(
                patient_id=int(row["patient_id"]),
                first_name=row["first_name"],
                last_name=row["last_name"],
                dob=parse_date(row["dob"]),
                gender=row["gender"] or None,
            )
            session.merge(patient)
    
    session.flush()
    print(f"✅ Loaded {len(rows)} patients")

def load_encounters(session: Session, path: str) -> None:
    """Load encounters with ML features from CSV"""
    print(f"\nLoading encounters from {path}...")
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        print(f"Read {len(rows)} encounter rows")
        
        loaded = 0
        for row in rows:
            patient_id = int(row["patient_id"])
            
            # Verify patient exists
            patient = session.get(Patient, patient_id)
            if not patient:
                print(f"⚠️ Patient {patient_id} not found, skipping encounter")
                continue
            
            # Create encounter with all 15 ML features
            encounter = Encounter(
                encounter_id=int(row["encounter_id"]),
                patient_id=patient_id,
                admit_date=parse_date(row["admit_date"]),
                discharge_date=parse_date(row["discharge_date"]),
                diagnosis=row.get("diagnosis"),
                
                # ML Features (from Phase 2 feature engineering)
                age_years_cleaned=float(row["age_years_cleaned"]),
                gender_M=int(row["gender_M"]),
                los_days=float(row["los_days"]),
                previous_admissions=int(row["previous_admissions"]),
                days_since_last_admit=float(row["days_since_last_admit"]),
                diagnosis_count=int(row["diagnosis_count"]),
                charlson_score=int(row["charlson_score"]),
                procedure_count=int(row["procedure_count"]),
                icu_stay_count=int(row["icu_stay_count"]),
                icu_los_days=float(row["icu_los_days"]),
                admit_type_EMERGENCY=int(row["admit_type_EMERGENCY"]),
                admit_type_URGENT=int(row["admit_type_URGENT"]),
                insurance_Medicare=int(row["insurance_Medicare"]),
                insurance_Private=int(row["insurance_Private"]),
                hospital_expire_flag=int(row["hospital_expire_flag"]),
                
                # Risk scores (will be computed by XGBoost later)
                risk_score=None,
                risk_level=None
            )
            session.merge(encounter)
            loaded += 1
        
        session.flush()
        print(f"✅ Loaded {loaded} encounters")

def main() -> None:
    """Main ETL pipeline"""
    print("=" * 60)
    print("📂 Loading Synthetic EHR Data")
    print("=" * 60)
    
    # Create tables if they don't exist
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        load_patients(db, "data/patients.csv")
        load_encounters(db, "data/encounters.csv")
        db.commit()
        
        print("\n" + "=" * 60)
        print("✅ Data loading complete!")
        print("=" * 60)
        print("\n📊 Next steps:")
        print("1. Run: curl -X POST 'http://localhost:8000/predict/batch/recompute'")
        print("2. Then: curl 'http://localhost:8000/ward/risk'")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
