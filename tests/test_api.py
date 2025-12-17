from fastapi.testclient import TestClient
from app.main import app
from app.db import Base, engine, SessionLocal
from app.models import Patient, Encounter, Task
from datetime import date

client = TestClient(app)

# Setup: ensure tables exist
Base.metadata.create_all(bind=engine)


def setup_test_data():
    """Add test patient and encounter for prediction/ward tests"""
    db = SessionLocal()
    try:
        # Check if data already exists
        existing = db.query(Patient).filter(Patient.id == 999).first()
        if existing:
            return
        
        patient = Patient(
            id=999,
            first_name="Test",
            last_name="Patient",
            birth_date=date(1950, 1, 1),
            gender="M",
        )
        db.add(patient)
        
        encounter = Encounter(
            id=999,
            patient_id=999,
            encounter_type="IPD",
            start_date=date(2025, 12, 1),
            end_date=date(2025, 12, 10),
            risk_score=0.8,
            risk_level="high",
        )
        db.add(encounter)
        
        task = Task(
            id=999,
            patient_id=999,
            encounter_id=999,
            task_type="nurse_review",
            status="open",
        )
        db.add(task)
        
        db.commit()
    finally:
        db.close()


setup_test_data()


def get_auth_token():
    """Helper to get auth token for tests"""
    # Register if not exists
    register_payload = {
        "username": "testuser",
        "password": "testpass123",
        "full_name": "Test User",
        "role": "nurse",
    }
    client.post("/auth/register", json=register_payload)
    
    # Login
    login_data = {"username": "testuser", "password": "testpass123"}
    response = client.post("/auth/login", data=login_data)
    return response.json()["access_token"]


# ===== Basic Health Check =====

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# ===== Auth Tests =====

def test_register_and_login():
    register_payload = {
        "username": "newuser",
        "password": "testpass123",
        "full_name": "New User",
        "role": "doctor",
    }
    response = client.post("/auth/register", json=register_payload)
    assert response.status_code == 200
    assert response.json()["username"] == "newuser"

    login_data = {"username": "newuser", "password": "testpass123"}
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_login_invalid_credentials():
    login_data = {"username": "fake", "password": "fake"}
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 400


# ===== Patients Tests =====

def test_patients_without_auth():
    response = client.get("/patients")
    assert response.status_code == 401


def test_patients_with_auth():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/patients", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_patient_by_id():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/patients/999", headers=headers)
    assert response.status_code == 200
    assert response.json()["first_name"] == "Test"


def test_get_patient_not_found():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/patients/99999", headers=headers)
    assert response.status_code == 404


# ===== Ward Risk Tests =====

def test_ward_risk_without_auth():
    response = client.get("/ward/risk")
    assert response.status_code == 401


def test_ward_risk_with_auth():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/ward/risk", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    # Should include our test patient with risk data
    data = response.json()
    assert len(data) > 0
    assert all("risk_score" in item for item in data)
    assert all("los_days" in item for item in data)


def test_ward_risk_filter_by_high():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/ward/risk?min_level=high", headers=headers)
    assert response.status_code == 200
    data = response.json()
    # All returned patients should be high risk
    for item in data:
        assert item["risk_level"] == "high"


# ===== Tasks Tests =====

def test_tasks_without_auth():
    response = client.get("/tasks")
    assert response.status_code == 401


def test_tasks_with_auth():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/tasks", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_tasks_filter_by_status():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Get open tasks
    response = client.get("/tasks?status_filter=open", headers=headers)
    assert response.status_code == 200
    data = response.json()
    for task in data:
        assert task["status"] == "open"


def test_complete_task():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    
    # Complete task 999
    response = client.post("/tasks/999/complete", headers=headers)
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
    assert response.json()["completed_at"] is not None


def test_complete_task_not_found():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    response = client.post("/tasks/99999/complete", headers=headers)
    assert response.status_code == 404


# ===== Prediction Tests =====

def test_predict_readmission_without_auth():
    payload = {"patient_id": 999, "encounter_id": 999}
    response = client.post("/predict/readmission", json=payload)
    assert response.status_code == 401


def test_predict_readmission_with_auth():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"patient_id": 999, "encounter_id": 999}
    response = client.post("/predict/readmission", json=payload, headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "risk_score" in data
    assert "risk_level" in data
    assert data["patient_id"] == 999
    assert data["encounter_id"] == 999


def test_predict_readmission_patient_not_found():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"patient_id": 99999, "encounter_id": 999}
    response = client.post("/predict/readmission", json=payload, headers=headers)
    assert response.status_code == 404


def test_predict_readmission_encounter_not_found():
    token = get_auth_token()
    headers = {"Authorization": f"Bearer {token}"}
    payload = {"patient_id": 999, "encounter_id": 99999}
    response = client.post("/predict/readmission", json=payload, headers=headers)
    assert response.status_code == 404
