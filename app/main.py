from datetime import datetime, timedelta

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from sqlalchemy import desc
from sqlalchemy.orm import Session

from jose import JWTError, jwt

from app.db import Base, engine, SessionLocal
from app.models import Patient, Encounter, Task, User
from app.schemas import (
    PatientOut,
    WardPatientOut,
    TaskOut,
    PredictReadmissionRequest,
    PredictReadmissionResponse,
    UserCreate,
    UserOut,
    Token,
)
from app.risk import calculate_readmission_risk
from app.auth import (
    verify_password,
    get_password_hash,
    create_access_token,
    get_user_claims,
    SECRET_KEY,
    ALGORITHM,
)


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

app = FastAPI(title="AI EHR Predictor MVP")

# Create tables (OK for dev; later use Alembic)
Base.metadata.create_all(bind=engine)


# ---------- DB + USER HELPERS ----------

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_user_by_username(db: Session, username: str) -> User | None:
    return db.query(User).filter(User.username == username).first()


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        role: str | None = payload.get("role")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = get_user_by_username(db, username=username)
    if user is None or not user.is_active:
        raise credentials_exception
    return user


def require_role(required_roles: list[str]):
    def _inner(user: User = Depends(get_current_user)):
        if user.role not in required_roles:
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return user

    return _inner


# ---------- AUTH ENDPOINTS ----------

@app.post("/auth/register", response_model=UserOut)
def register_user(payload: UserCreate, db: Session = Depends(get_db)):
    # dev-only open registration; later, restrict to admins
    existing = get_user_by_username(db, payload.username)
    if existing:
        raise HTTPException(status_code=400, detail="Username already registered")

    user = User(
        username=payload.username,
        full_name=payload.full_name,
        hashed_password=get_password_hash(payload.password),
        role=payload.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post("/auth/login", response_model=Token)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = get_user_by_username(db, form_data.username)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    claims = get_user_claims(user)
    access_token = create_access_token(data=claims)
    return Token(access_token=access_token, token_type="bearer")


# ---------- BASIC HEALTHCHECK ----------

@app.get("/health")
def health_check():
    return {"status": "ok"}


# ---------- PATIENT ENDPOINTS ----------

@app.get("/patients", response_model=list[PatientOut])
def list_patients(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["nurse", "doctor", "admin"])),
):
    return db.query(Patient).all()


@app.get("/patients/{patient_id}", response_model=PatientOut)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["nurse", "doctor", "admin"])),
):
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient


# ---------- WARD RISK / WORKFLOW ----------

@app.get("/ward/risk", response_model=list[WardPatientOut])
def ward_risk(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["nurse", "doctor", "admin"])),
):
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

    return [
        WardPatientOut(
            patient_id=r.patient_id,
            first_name=r.first_name,
            last_name=r.last_name,
            risk_score=r.risk_score or 0.0,
            risk_level=r.risk_level or "unknown",
        )
        for r in rows
    ]


@app.get("/tasks", response_model=list[TaskOut])
def list_tasks(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["nurse", "doctor", "admin"])),
):
    tasks = db.query(Task).order_by(desc(Task.created_at)).all()
    return tasks


@app.post("/tasks/{task_id}/complete", response_model=TaskOut)
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
    db.commit()
    db.refresh(task)
    return task


# ---------- PREDICTION ENDPOINT ----------

@app.post("/predict/readmission", response_model=PredictReadmissionResponse)
def predict_readmission(
    payload: PredictReadmissionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_role(["nurse", "doctor", "admin"])),
):
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

    # store on encounter
    encounter.risk_score = score
    encounter.risk_level = level
    db.commit()
    db.refresh(encounter)

    # if high risk, ensure there is an open nurse_review task
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
