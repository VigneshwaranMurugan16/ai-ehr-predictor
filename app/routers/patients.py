from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.models import Patient, User
from app.schemas import PatientOut
from app.services.security import get_db, require_role, log_action

router = APIRouter(prefix="/patients", tags=["patients"])


@router.get("", response_model=list[PatientOut])
def list_patients(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["nurse", "doctor", "admin"])),
):
    log_action(db, user, "LIST_PATIENTS", details=None)
    patients = db.query(Patient).all()
    db.commit()
    return patients


@router.get("/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["nurse", "doctor", "admin"])),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    log_action(db, user, "VIEW_PATIENT", details=f"patient_id={patient_id}")
    db.commit()
    return patient
