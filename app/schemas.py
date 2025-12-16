from datetime import date, datetime
from pydantic import BaseModel

class PatientOut(BaseModel):
    id: int
    first_name: str
    last_name: str
    birth_date: date | None = None
    gender: str | None = None

    class Config:
        orm_mode = True




class WardPatientOut(BaseModel):
    patient_id: int
    first_name: str
    last_name: str
    risk_score: float
    risk_level: str
    los_days: int | None = None
    los_level: str | None = None

    class Config:
        orm_mode = True



class TaskOut(BaseModel):
    id: int
    patient_id: int
    encounter_id: int
    task_type: str
    status: str
    created_at: datetime | None = None
    completed_at: datetime | None = None

    class Config:
        orm_mode = True
from datetime import date, datetime
from pydantic import BaseModel

# existing PatientOut, WardPatientOut, TaskOut...

class UserCreate(BaseModel):
    username: str
    full_name: str | None = None
    password: str
    role: str = "nurse"  # default


class UserOut(BaseModel):
    id: int
    username: str
    full_name: str | None = None
    role: str

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: str | None = None
    role: str | None = None


class PredictReadmissionRequest(BaseModel):
    patient_id: int
    encounter_id: int


class PredictReadmissionResponse(BaseModel):
    patient_id: int
    encounter_id: int
    risk_score: float
    risk_level: str
