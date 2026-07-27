from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Optional

from ..agents.recommendation import RecommendationAgent
from ..agents.risk_evaluation import RiskEvaluationAgent
from ..agents.supervisor import SupervisorAgent
from ..agents.trend_detection import TrendDetectionAgent
from ..agents.vital_analysis import VitalAnalysisAgent
from ..core.profiles import PATIENT_BY_ID, PATIENT_PROFILES, PatientProfile
from ..models.schemas import (
    DatasetUploadResponse,
    OverviewResponse,
    PatientDetail,
    PatientDetailResponse,
    PatientSummary,
    SystemSummary,
    TrendSummary,
    VitalSnapshot,
)
from .dataset_loader import load_dataset
from .simulation import VitalSample, next_sample, now_utc, seeded_series


@dataclass
class PatientRuntimeState:
    profile: PatientProfile
    samples: deque[VitalSample]
    spike_ticks: int = 0
    source: str = "simulation"
    source_label: str = "Simulated digital twin"
    dataset_series: list[VitalSample] = field(default_factory=list)
    dataset_cursor: int = 0


class DigitalTwinService:
    def __init__(self) -> None:
        self._lock = Lock()
        self._step_interval = timedelta(seconds=2.5)
        self._last_advanced = now_utc()
        self._tick = 0
        self._supervisor = SupervisorAgent(
            vital_agent=VitalAnalysisAgent(),
            trend_agent=TrendDetectionAgent(),
            risk_agent=RiskEvaluationAgent(),
            recommendation_agent=RecommendationAgent(),
        )
        self._states = self._seed_states()

    def _seed_states(self) -> dict[str, PatientRuntimeState]:
        states: dict[str, PatientRuntimeState] = {}
        for profile in PATIENT_PROFILES:
            states[profile.id] = PatientRuntimeState(
                profile=profile,
                samples=deque(seeded_series(profile), maxlen=24),
            )
        return states

    def reset(self) -> None:
        with self._lock:
            self._states = self._seed_states()
            self._tick = 0
            self._last_advanced = now_utc()

    def ensure_fresh(self) -> None:
        with self._lock:
            now = now_utc()
            while self._last_advanced + self._step_interval <= now:
                self._step_once()
                self._last_advanced += self._step_interval

    def _step_once(self) -> None:
        self._tick += 1
        for state in self._states.values():
            if state.dataset_series:
                if state.dataset_cursor >= len(state.dataset_series):
                    state.dataset_cursor = 0
                sample = state.dataset_series[state.dataset_cursor]
                state.dataset_cursor = (state.dataset_cursor + 1) % len(state.dataset_series)
                state.samples.append(
                    VitalSample(
                        time=now_utc(),
                        spo2=sample.spo2,
                        heart_rate=sample.heart_rate,
                        temperature=sample.temperature,
                    )
                )
            else:
                previous = state.samples[-1]
                spiking = state.spike_ticks > 0
                state.samples.append(next_sample(state.profile, previous, self._tick + len(state.samples), spiking))
                if state.spike_ticks > 0:
                    state.spike_ticks -= 1

    def simulate_spike(self, patient_id: str) -> None:
        if patient_id not in self._states:
            raise KeyError(f"Unknown patient {patient_id}")
        with self._lock:
            self._states[patient_id].spike_ticks = 5
            self._step_once()
            self._last_advanced = now_utc()

    def _evaluation_for(self, patient_id: str) -> dict:
        state = self._states[patient_id]
        return self._supervisor.run(state.profile, list(state.samples))

    def _detail_from_evaluation(self, patient_id: str, evaluation: dict) -> PatientDetail:
        state = self._states[patient_id]
        latest = evaluation["latest"]
        risk = evaluation["risk_evaluation"]
        recommendation = evaluation["recommendation"]
        trend = evaluation["trend_analysis"]

        return PatientDetail(
            id=state.profile.id,
            name=state.profile.name,
            age=state.profile.age,
            bed=state.profile.bed,
            source=state.source,
            source_label=state.source_label,
            baseline_condition=state.profile.default_condition,
            current_condition=risk["current_condition"],
            risk_label=risk["label"],
            risk_score=risk["score"],
            tone=risk["tone"],
            latest_vitals=VitalSnapshot(
                time=latest.time,
                heart_rate=round(latest.heart_rate, 2),
                spo2=round(latest.spo2, 2),
                temperature=round(latest.temperature, 2),
            ),
            alerts=recommendation["alerts"],
            prediction=recommendation["prediction"],
            danger_text=risk["danger_text"],
            action=recommendation["action"],
            reasons=recommendation["reasons"],
            trend_summary=TrendSummary(
                spo2=round(trend["spo2_slope"], 2),
                heart_rate=round(trend["heart_slope"], 2),
                temperature=round(trend["temp_slope"], 2),
            ),
            history=[
                VitalSnapshot(
                    time=sample.time,
                    heart_rate=round(sample.heart_rate, 2),
                    spo2=round(sample.spo2, 2),
                    temperature=round(sample.temperature, 2),
                )
                for sample in list(state.samples)
            ],
        )

    def _summary_from_detail(self, detail: PatientDetail) -> PatientSummary:
        return PatientSummary(
            id=detail.id,
            name=detail.name,
            age=detail.age,
            bed=detail.bed,
            source=detail.source,
            source_label=detail.source_label,
            current_condition=detail.current_condition,
            risk_label=detail.risk_label,
            risk_score=detail.risk_score,
            tone=detail.tone,
            latest_vitals=detail.latest_vitals,
            alerts=detail.alerts,
        )

    def _system_summary(self, details: list[PatientDetail]) -> SystemSummary:
        stable_count = len([detail for detail in details if detail.risk_label == "Stable"])
        moderate_count = len([detail for detail in details if detail.risk_label == "Moderate"])
        critical_count = len([detail for detail in details if detail.risk_label == "Critical"])
        priority_patient = max(details, key=lambda detail: detail.risk_score)

        return SystemSummary(
            stable_count=stable_count,
            moderate_count=moderate_count,
            critical_count=critical_count,
            notification_count=critical_count,
            priority_patient_id=priority_patient.id,
            priority_message=(
                f"Priority focus: {priority_patient.id} {priority_patient.name} is currently "
                f"{priority_patient.risk_label.lower()} with a score of {priority_patient.risk_score}/100."
            ),
        )

    def get_overview(self) -> OverviewResponse:
        self.ensure_fresh()
        with self._lock:
            details = [self._detail_from_evaluation(patient_id, self._evaluation_for(patient_id)) for patient_id in self._states]
            system_summary = self._system_summary(details)
            priority_patient = max(details, key=lambda detail: detail.risk_score)
            patients = [self._summary_from_detail(detail) for detail in details]

        return OverviewResponse(
            generated_at=now_utc(),
            system_summary=system_summary,
            priority_patient=priority_patient,
            patients=patients,
        )

    def get_patient_detail(self, patient_id: str) -> PatientDetailResponse:
        if patient_id not in PATIENT_BY_ID:
            raise KeyError(f"Unknown patient {patient_id}")

        self.ensure_fresh()
        with self._lock:
            details = [self._detail_from_evaluation(pid, self._evaluation_for(pid)) for pid in self._states]
            system_summary = self._system_summary(details)
            detail = next(item for item in details if item.id == patient_id)
            patients = [self._summary_from_detail(item) for item in details]

        return PatientDetailResponse(
            generated_at=now_utc(),
            system_summary=system_summary,
            patient=detail,
            patients=patients,
        )

    def upload_dataset(
        self,
        file_path: Path,
        patient_column: Optional[str] = None,
        timestamp_column: Optional[str] = None,
        heart_rate_column: Optional[str] = None,
        spo2_column: Optional[str] = None,
        temperature_column: Optional[str] = None,
    ) -> DatasetUploadResponse:
        load_result = load_dataset(
            file_path=file_path,
            patient_column=patient_column,
            timestamp_column=timestamp_column,
            heart_rate_column=heart_rate_column,
            spo2_column=spo2_column,
            temperature_column=temperature_column,
        )

        source_items = list(load_result.series_by_source_id.items())
        assigned_patients: list[str] = []

        with self._lock:
            self._states = self._seed_states()
            for runtime_state, (source_id, series) in zip(self._states.values(), source_items):
                runtime_state.dataset_series = series
                runtime_state.source = "dataset"
                runtime_state.source_label = f"CSV dataset source {source_id}"
                runtime_state.samples = deque(series[: min(24, len(series))], maxlen=24)
                runtime_state.dataset_cursor = min(24, len(series))
                assigned_patients.append(runtime_state.profile.id)
            self._tick = 0
            self._last_advanced = now_utc()

        return DatasetUploadResponse(
            message=(
                f"Loaded {load_result.rows_loaded} rows and assigned dataset-backed vitals to "
                f"{len(assigned_patients)} patient twin(s)."
            ),
            assigned_patients=assigned_patients,
            rows_loaded=load_result.rows_loaded,
            detected_columns=load_result.detected_columns,
        )


digital_twin_service = DigitalTwinService()
