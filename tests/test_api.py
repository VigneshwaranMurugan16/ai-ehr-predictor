from fastapi.testclient import TestClient
from app.main import app
from app.db import Base, engine

client = TestClient(app)

# Setup: ensure tables exist (in-memory or test DB would be better later)
Base.metadata.create_all(bind=engine)


def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_register_and_login():
    # Register a test user
    register_payload = {
        "username": "testuser",
        "password": "testpass123",
        "full_name": "Test User",
        "role": "nurse",
    }
    response = client.post("/auth/register", json=register_payload)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

    # Login
    login_data = {"username": "testuser", "password": "testpass123"}
    response = client.post("/auth/login", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_patients_without_auth():
    response = client.get("/patients")
    assert response.status_code == 401  # unauthorized


def test_patients_with_auth():
    # Login first
    login_data = {"username": "testuser", "password": "testpass123"}
    response = client.post("/auth/login", data=login_data)
    token = response.json()["access_token"]

    # Call protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/patients", headers=headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
