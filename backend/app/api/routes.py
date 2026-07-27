from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from ..models.schemas import DatasetUploadResponse, OverviewResponse, PatientDetailResponse, SimpleMessage
from ..services.digital_twin import digital_twin_service

router = APIRouter(prefix="/api", tags=["meditwin"])


@router.get("/health", response_model=SimpleMessage)
def healthcheck() -> SimpleMessage:
    return SimpleMessage(message="MediTwin backend is running.")


@router.get("/overview", response_model=OverviewResponse)
def get_overview() -> OverviewResponse:
    return digital_twin_service.get_overview()


@router.get("/patients/{patient_id}", response_model=PatientDetailResponse)
def get_patient(patient_id: str) -> PatientDetailResponse:
    try:
        return digital_twin_service.get_patient_detail(patient_id.upper())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/patients/{patient_id}/simulate-spike", response_model=SimpleMessage)
def simulate_spike(patient_id: str) -> SimpleMessage:
    try:
        digital_twin_service.simulate_spike(patient_id.upper())
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return SimpleMessage(message=f"Spike simulation triggered for {patient_id.upper()}.")


@router.post("/reset", response_model=SimpleMessage)
def reset_system() -> SimpleMessage:
    digital_twin_service.reset()
    return SimpleMessage(message="Simulation reset to baseline state.")


@router.post("/datasets/upload", response_model=DatasetUploadResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    patient_column: Optional[str] = Form(default=None),
    timestamp_column: Optional[str] = Form(default=None),
    heart_rate_column: Optional[str] = Form(default=None),
    spo2_column: Optional[str] = Form(default=None),
    temperature_column: Optional[str] = Form(default=None),
) -> DatasetUploadResponse:
    upload_dir = Path(__file__).resolve().parents[2] / "data" / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    target_path = upload_dir / file.filename
    content = await file.read()
    target_path.write_bytes(content)

    try:
        return digital_twin_service.upload_dataset(
            file_path=target_path,
            patient_column=patient_column,
            timestamp_column=timestamp_column,
            heart_rate_column=heart_rate_column,
            spo2_column=spo2_column,
            temperature_column=temperature_column,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
