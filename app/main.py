from fastapi import FastAPI

app = FastAPI(title="AI EHR Predictor MVP")

@app.get("/health")
def health_check():
    return {"status": "ok"}
    