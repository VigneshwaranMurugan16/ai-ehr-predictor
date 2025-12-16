from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.models import Patient, Encounter, Task, User
from app.schemas import (
    WardPatientOut,
    TaskOut,
    PredictReadmissionRequest,
    PredictReadmissionResponse,
)
from app.risk import calculate_readmission_risk, calculate_los_risk
from app.services.security import get_db, require_role, log_action

router = APIRouter(tags=["ward", "tasks", "prediction"])

RISK_LEVEL_ORDER = {"low": 1, "medium": 2, "high": 3}


@router.get("/ward/risk", response_model=list[WardPatientOut])
def ward_risk(
    min_level: str | None = Query(
        None,
        description="Filter by minimum readmission risk level: low, medium, high",
    ),
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["nurse", "doctor", "admin"])),
):
    log_action(db, user, "VIEW_WARD", details=f"min_level={min_level}")

    rows = (
        db.query(
            Encounter.patient_id,
            Patient.first_name,
            Patient.last_name,
            Encounter.risk_score,
            Encounter.risk_level,
        )
        .join(Patient, Patient.id == Encounter.patient_id)
        .order_by(desc(Encounter.risk_score))
        .all()
    )

    results: list[WardPatientOut] = []
    for r in rows:
        level = r.risk_level or "unknown"
        score = r.risk_score or 0.0

        # find matching encounter to compute LOS
        enc = (
            db.query(Encounter)
            .filter(
                Encounter.patient_id == r.patient_id,
                Encounter.risk_score == r.risk_score,
                Encounter.risk_level == r.risk_level,
            )
            .first()
        )
        los_days, los_level = (None, "unknown")
        if enc:
            los_days, los_level = calculate_los_risk(enc)

        # apply optional readmission-risk filter
        if min_level is not None and min_level in RISK_LEVEL_ORDER:
            if level in RISK_LEVEL_ORDER:
                if RISK_LEVEL_ORDER[level] < RISK_LEVEL_ORDER[min_level]:
                    continue
            else:
                # unknown levels are treated as lowest risk
                continue

        results.append(
            WardPatientOut(
                patient_id=r.patient_id,
                first_name=r.first_name,
                last_name=r.last_name,
                risk_score=score,
                risk_level=level,
                los_days=los_days,
                los_level=los_level,
            )
        )

    db.commit()
    return results


@router.get("/tasks", response_model=list[TaskOut])
def list_tasks(
    status_filter: str | None = Query(
        None,
        description="Filter by status: open or completed",
    ),
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["nurse", "doctor", "admin"])),
):
    log_action(db, user, "LIST_TASKS", details=f"status_filter={status_filter}")

    query = db.query(Task).order_by(desc(Task.created_at))
    if status_filter in ("open", "completed"):
        query = query.filter(Task.status == status_filter)
    tasks = query.all()
    db.commit()
    return tasks


@router.post("/tasks/{task_id}/complete", response_model=TaskOut)
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["nurse", "doctor", "admin"])),
):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = "completed"
    task.completed_at = datetime.utcnow()
    log_action(db, user, "COMPLETE_TASK", details=f"task_id={task_id}")
    db.commit()
    db.refresh(task)
    return task


@router.post("/predict/readmission", response_model=PredictReadmissionResponse)
def predict_readmission(
    payload: PredictReadmissionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["nurse", "doctor", "admin"])),
):
    log_action(
        db,
        user,
        "PREDICT_READMISSION",
        details=f"patient_id={payload.patient_id},encounter_id={payload.encounter_id}",
    )

    patient = db.query(Patient).filter(Patient.id == payload.patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")

    encounter = (
        db.query(Encounter)
        .filter(
            Encounter.id == payload.encounter_id,
            Encounter.patient_id == patient.id,
        )
        .first()
    )
    if not encounter:
        raise HTTPException(status_code=404, detail="Encounter not found for this patient")

    score, level = calculate_readmission_risk(patient, encounter)

    encounter.risk_score = score
    encounter.risk_level = level
    db.commit()
    db.refresh(encounter)

    if level == "high":
        existing_task = (
            db.query(Task)
            .filter(
                Task.patient_id == patient.id,
                Task.encounter_id == encounter.id,
                Task.task_type == "nurse_review",
                Task.status == "open",
            )
            .first()
        )
        if not existing_task:
            new_task = Task(
                patient_id=patient.id,
                encounter_id=encounter.id,
                task_type="nurse_review",
                status="open",
            )
            db.add(new_task)
            db.commit()

    return PredictReadmissionResponse(
        patient_id=patient.id,
        encounter_id=encounter.id,
        risk_score=score,
        risk_level=level,
    )
