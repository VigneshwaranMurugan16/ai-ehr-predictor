# app/models.py
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db import Base


class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)


class Patient(Base):
    __tablename__ = "patients"
    
    patient_id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    dob = Column(Date)
    gender = Column(String)
    
    encounters = relationship("Encounter", back_populates="patient")


class Encounter(Base):
    __tablename__ = "encounters"
    
    encounter_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"))
    admit_date = Column(Date)
    discharge_date = Column(Date)
    diagnosis = Column(String)
    
    # ML Features (15 features for XGBoost)
    age_years_cleaned = Column(Float)
    gender_M = Column(Integer)
    los_days = Column(Float)
    previous_admissions = Column(Integer)
    days_since_last_admit = Column(Float)
    diagnosis_count = Column(Integer)
    charlson_score = Column(Integer)
    procedure_count = Column(Integer)
    icu_stay_count = Column(Integer)
    icu_los_days = Column(Float)
    admit_type_EMERGENCY = Column(Integer)
    admit_type_URGENT = Column(Integer)
    insurance_Medicare = Column(Integer)
    insurance_Private = Column(Integer)
    hospital_expire_flag = Column(Integer)
    
    # Risk predictions (computed by XGBoost)
    risk_score = Column(Float)
    risk_level = Column(String)
    
    patient = relationship("Patient", back_populates="encounters")


class Task(Base):
    __tablename__ = "tasks"
    
    task_id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.patient_id"))
    encounter_id = Column(Integer, ForeignKey("encounters.encounter_id"))
    task_type = Column(String)
    status = Column(String, default="open")
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String)
    resource = Column(String, nullable=True)
    details = Column(String, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
