from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import HTTPException
from pathlib import Path

from .api.routes import router


app = FastAPI(
    title="MediTwin Multi-Agent Backend",
    version="0.1.0",
    description="Digital twin backend for ICU-style multi-patient monitoring and explainable AI support.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

FRONTEND_DIR = Path(__file__).resolve().parents[2]


@app.get("/", include_in_schema=False)
def serve_dashboard() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/index.html", include_in_schema=False)
def serve_dashboard_file() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")


@app.get("/patients/{patient_id}", include_in_schema=False)
def serve_patient_page(patient_id: str) -> FileResponse:
    normalized = patient_id.strip().lower()
    target = FRONTEND_DIR / f"patient-{normalized}.html"
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"No patient page found for {patient_id}.")
    return FileResponse(target)


@app.get("/styles.css", include_in_schema=False)
def serve_styles() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "styles.css")


@app.get("/script.js", include_in_schema=False)
def serve_script() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "script.js")
