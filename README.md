# MediTwin Prototype 2026

This project now includes:

- A multi-page clinician frontend for overview plus separate patient pages
- A Python FastAPI backend with a real multi-agent structure
- Agents for vital analysis, trend detection, risk evaluation, and recommendation
- Digital twin state management for six ICU-style patients
- CSV upload support for a primary ICU vitals prototype dataset
- Explainable risk classification, anomaly alerts, and action guidance

## Frontend

Open [index.html](C:\Users\vijet\OneDrive\Desktop\MediTwin 1st prototype 2026\index.html) in a browser.

## Backend setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r backend/requirements.txt
```

3. Start the API:

```bash
python backend/run.py
```

The backend runs at `http://127.0.0.1:8000`.

## Key API routes

- `GET /api/overview`
- `GET /api/patients/{patient_id}`
- `POST /api/patients/{patient_id}/simulate-spike`
- `POST /api/reset`
- `POST /api/datasets/upload`

## CSV upload prototype

Upload a CSV to `POST /api/datasets/upload` using form-data with `file`.

Optional form fields if your dataset uses different names:

- `patient_column`
- `timestamp_column`
- `heart_rate_column`
- `spo2_column`
- `temperature_column`

## Files

- [index.html](C:\Users\vijet\OneDrive\Desktop\MediTwin 1st prototype 2026\index.html)
- [styles.css](C:\Users\vijet\OneDrive\Desktop\MediTwin 1st prototype 2026\styles.css)
- [script.js](C:\Users\vijet\OneDrive\Desktop\MediTwin 1st prototype 2026\script.js)
- [backend/app/main.py](C:\Users\vijet\OneDrive\Desktop\MediTwin 1st prototype 2026\backend\app\main.py)
- [backend/requirements.txt](C:\Users\vijet\OneDrive\Desktop\MediTwin 1st prototype 2026\backend\requirements.txt)
