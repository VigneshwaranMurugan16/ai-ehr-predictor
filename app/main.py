from fastapi import FastAPI

from app.db import Base, engine
from app.routers import auth, patients, ward


app = FastAPI(title="AI EHR Predictor MVP")

# Create tables (dev only)
Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}


# Mount routers
app.include_router(auth.router)
app.include_router(patients.router)
app.include_router(ward.router)
