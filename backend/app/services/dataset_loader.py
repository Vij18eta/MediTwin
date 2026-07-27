from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import pandas as pd

from .simulation import VitalSample


@dataclass
class DatasetLoadResult:
    series_by_source_id: dict[str, list[VitalSample]]
    rows_loaded: int
    detected_columns: dict[str, Optional[str]]


ALIASES = {
    "patient_id": ["patient_id", "subject_id", "stay_id", "icustay_id", "patient", "id"],
    "timestamp": ["charttime", "timestamp", "time", "datetime", "recorded_at"],
    "heart_rate": ["heart_rate", "heartrate", "hr", "pulse"],
    "spo2": ["spo2", "sp02", "oxygen_saturation", "o2sat", "sao2"],
    "temperature": ["temperature", "temp", "temperature_c", "body_temp"],
}


def normalize_column_name(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def fahrenheit_to_celsius(value: float) -> float:
    return (value - 32.0) * 5.0 / 9.0


def normalize_temperature_series(series: pd.Series) -> pd.Series:
    normalized = series.copy()

    # Temperatures above 45 are assumed to be Fahrenheit and converted to Celsius.
    fahrenheit_mask = normalized > 45
    normalized.loc[fahrenheit_mask] = normalized.loc[fahrenheit_mask].apply(fahrenheit_to_celsius)
    return normalized


def clean_vitals(frame: pd.DataFrame, heart_col: str, spo2_col: str, temp_col: str) -> pd.DataFrame:
    cleaned = frame.copy()
    cleaned[temp_col] = normalize_temperature_series(cleaned[temp_col])

    cleaned = cleaned[
        cleaned[heart_col].between(25, 220)
        & cleaned[spo2_col].between(60, 100)
        & cleaned[temp_col].between(30.0, 43.0)
    ]

    return cleaned


def detect_column(frame: pd.DataFrame, explicit: Optional[str], key: str) -> Optional[str]:
    if explicit and explicit in frame.columns:
        return explicit

    normalized = {normalize_column_name(column): column for column in frame.columns}
    for alias in ALIASES[key]:
        if alias in normalized:
            return normalized[alias]
    return None


def load_dataset(
    file_path: Path,
    patient_column: Optional[str] = None,
    timestamp_column: Optional[str] = None,
    heart_rate_column: Optional[str] = None,
    spo2_column: Optional[str] = None,
    temperature_column: Optional[str] = None,
) -> DatasetLoadResult:
    frame = pd.read_csv(file_path)
    if frame.empty:
        raise ValueError("The uploaded CSV is empty.")

    patient_col = detect_column(frame, patient_column, "patient_id")
    timestamp_col = detect_column(frame, timestamp_column, "timestamp")
    heart_col = detect_column(frame, heart_rate_column, "heart_rate")
    spo2_col = detect_column(frame, spo2_column, "spo2")
    temp_col = detect_column(frame, temperature_column, "temperature")

    missing = [key for key, column in {
        "heart_rate": heart_col,
        "spo2": spo2_col,
        "temperature": temp_col,
    }.items() if column is None]
    if missing:
        raise ValueError(
            "Missing required columns for: " + ", ".join(missing)
            + ". Provide explicit mappings or upload a dataset with these fields."
        )

    if patient_col is None:
        frame["__patient_id__"] = "uploaded_patient_1"
        patient_col = "__patient_id__"

    if timestamp_col is None:
        frame["__generated_time__"] = pd.date_range(end=pd.Timestamp.utcnow(), periods=len(frame), freq="min", tz="UTC")
        timestamp_col = "__generated_time__"

    frame = frame[[patient_col, timestamp_col, heart_col, spo2_col, temp_col]].copy()
    frame[heart_col] = pd.to_numeric(frame[heart_col], errors="coerce")
    frame[spo2_col] = pd.to_numeric(frame[spo2_col], errors="coerce")
    frame[temp_col] = pd.to_numeric(frame[temp_col], errors="coerce")
    frame = frame.dropna(subset=[heart_col, spo2_col, temp_col])
    frame = clean_vitals(frame, heart_col, spo2_col, temp_col)
    if frame.empty:
        raise ValueError("The uploaded CSV does not contain valid rows for heart rate, SpO2, and temperature.")

    parsed_time = pd.to_datetime(frame[timestamp_col], errors="coerce", utc=True)
    if parsed_time.isna().all():
        parsed_time = pd.date_range(end=pd.Timestamp.utcnow(), periods=len(frame), freq="min", tz="UTC")
    else:
        parsed_time = parsed_time.ffill().bfill()
    frame["__parsed_time__"] = parsed_time

    series_by_source_id: dict[str, list[VitalSample]] = {}
    for source_id, group in frame.groupby(patient_col):
        ordered = group.sort_values("__parsed_time__")
        ordered = ordered.drop_duplicates(subset=["__parsed_time__", heart_col, spo2_col, temp_col], keep="last")
        samples = [
            VitalSample(
                time=row["__parsed_time__"].to_pydatetime(),
                heart_rate=float(row[heart_col]),
                spo2=float(row[spo2_col]),
                temperature=float(row[temp_col]),
            )
            for _, row in ordered.iterrows()
        ]
        if len(samples) >= 6:
            series_by_source_id[str(source_id)] = samples

    if not series_by_source_id:
        raise ValueError("No patient sequence with at least 6 valid rows was found in the uploaded CSV.")

    return DatasetLoadResult(
        series_by_source_id=series_by_source_id,
        rows_loaded=len(frame),
        detected_columns={
            "patient_id": patient_col,
            "timestamp": timestamp_col,
            "heart_rate": heart_col,
            "spo2": spo2_col,
            "temperature": temp_col,
        },
    )
