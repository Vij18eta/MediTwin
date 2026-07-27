from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class VitalSnapshot(BaseModel):
    time: datetime
    heart_rate: float
    spo2: float
    temperature: float


class TrendSummary(BaseModel):
    spo2: float
    heart_rate: float
    temperature: float


class PatientSummary(BaseModel):
    id: str
    name: str
    age: int
    bed: str
    source: str
    source_label: str
    current_condition: str
    risk_label: str
    risk_score: int
    tone: str
    latest_vitals: VitalSnapshot
    alerts: List[str] = Field(default_factory=list)


class PatientDetail(PatientSummary):
    prediction: str
    danger_text: str
    action: str
    reasons: List[str] = Field(default_factory=list)
    trend_summary: TrendSummary
    baseline_condition: str
    history: List[VitalSnapshot] = Field(default_factory=list)


class SystemSummary(BaseModel):
    stable_count: int
    moderate_count: int
    critical_count: int
    notification_count: int
    priority_patient_id: str
    priority_message: str


class OverviewResponse(BaseModel):
    generated_at: datetime
    system_summary: SystemSummary
    priority_patient: PatientDetail
    patients: List[PatientSummary]


class PatientDetailResponse(BaseModel):
    generated_at: datetime
    system_summary: SystemSummary
    patient: PatientDetail
    patients: List[PatientSummary]


class SimpleMessage(BaseModel):
    message: str


class DatasetUploadResponse(BaseModel):
    message: str
    assigned_patients: List[str]
    rows_loaded: int
    detected_columns: Dict[str, Optional[str]]
