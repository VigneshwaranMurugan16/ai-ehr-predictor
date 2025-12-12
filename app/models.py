from sqlalchemy import Column, Integer, String, Date, Float, DateTime, Boolean
from datetime import datetime
from app.db import Base

class Patient(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    birth_date = Column(Date, nullable=True)
    gender = Column(String, nullable=True)


class Encounter(Base):
    __tablename__ = "encounters"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, index=True)
    encounter_type = Column(String, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    risk_score = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)


class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, index=True)
    encounter_id = Column(Integer, index=True)
    task_type = Column(String, nullable=False)
    status = Column(String, nullable=False, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, nullable=False, default="nurse")  # "nurse" / "doctor" / "admin"
    is_active = Column(Boolean, default=True)
