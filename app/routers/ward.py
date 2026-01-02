# app/routers/ward.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional

from app.models import Patient, Encounter, Task
from app.services.security import get_db, get_current_user, log_action

router = APIRouter(prefix="/ward", tags=["ward"])

@router.get("/risk")
def ward_risk(
    min_level: Optional[str] = Query(None, description="Filter by minimum risk level"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Get ward risk board - all patients with their latest encounter risk scores"""
    
    log_action(db, user, "VIEW_WARD", details=f"min_level={min_level}")
    
    # Query encounters with patient info
    query = (
        db.query(
            Encounter.encounter_id,
            Encounter.patient_id,
            Patient.first_name,
            Patient.last_name,
            Encounter.risk_score,
            Encounter.risk_level,
        )
        .join(Patient, Patient.patient_id == Encounter.patient_id)
        .filter(Encounter.risk_score.isnot(None))
    )
    
    # Apply risk filter
    if min_level:
        level_order = {"low": 1, "medium": 2, "high": 3}
        if min_level in level_order:
            min_value = level_order[min_level]
            valid_levels = [k for k, v in level_order.items() if v >= min_value]
            query = query.filter(Encounter.risk_level.in_(valid_levels))
    
    # Order by risk score descending
    query = query.order_by(Encounter.risk_score.desc())
    
    results = query.all()
    
    # Format response
    patients = []
    for row in results:
        patients.append({
            "encounter_id": row.encounter_id,
            "patient_id": row.patient_id,
            "first_name": row.first_name,
            "last_name": row.last_name,
            "risk_score": float(row.risk_score) if row.risk_score else 0.0,
            "risk_level": row.risk_level or "unknown",
        })
    
    return patients


@router.get("/tasks")
def list_tasks(
    status_filter: Optional[str] = Query(None, description="Filter by status: open, completed, or all"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """List all tasks for the nurse"""
    
    log_action(db, user, "LIST_TASKS", details=f"status_filter={status_filter}")
    
    # Query tasks
    query = db.query(Task)
    
    if status_filter and status_filter != "All":
        query = query.filter(Task.status == status_filter)
    
    # Order by created_at desc
    tasks = query.order_by(Task.created_at.desc()).all()
    
    # Format response
    result = []
    for task in tasks:
        result.append({
            "task_id": task.task_id,
            "patient_id": task.patient_id,
            "encounter_id": task.encounter_id,
            "task_type": task.task_type,
            "status": task.status,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
        })
    
    return result


@router.post("/tasks/{task_id}/complete")
def complete_task(
    task_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """Mark a task as completed"""
    
    task = db.query(Task).filter(Task.task_id == task_id).first()
    
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")
    
    if task.status == "completed":
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="Task already completed")
    
    # Update task
    from datetime import datetime
    task.status = "completed"
    task.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(task)
    
    log_action(db, user, "COMPLETE_TASK", details=f"task_id={task_id}")
    
    return {
        "task_id": task.task_id,
        "status": task.status,
        "completed_at": task.completed_at.isoformat() if task.completed_at else None,
    }
