# Himalayan Sentinel

**Himalayan Sentinel** is a Smart India Hackathon prototype for flash-flood decision support. It combines a Random Forest flood-risk model, a stateful environmental simulation, simulated edge-node telemetry, WebSocket updates, and a browser command centre for the Uttarakhand Alaknanda-Ganga corridor.

> **Prototype notice:** The training dataset is synthetic and all live telemetry is simulated. This project demonstrates a software and ML architecture; it is not a field-deployed warning system or an operational flood forecast.

## Features

- Backend-authoritative, sequence-numbered simulation snapshots.
- Deterministic demo mode with correlated rainfall, soil, discharge, river, and slope behaviour.
- Random Forest inference served through FastAPI.
- Live WebSocket dashboard with synchronized cards, charts, alerts, event chain, map markers, and node health.
- Proposed/simulated sensor locations around Joshimath, Rudraprayag, Srinagar, Devprayag, and Rishikesh.
- Risk and system-confidence shown separately: environmental risk is not evidence quality.

## Architecture

```text
Simulated edge nodes -> authoritative simulation tick -> Random Forest inference
          |                         |                         |
  node health / network      immutable snapshot         alert engine
          +-----------------------> WebSocket dashboard <----------+
```

Every dashboard update is derived from one canonical backend snapshot. The final chart point and each corresponding live value therefore use the same numeric source.

## Quick start

### 1. Create an environment and install dependencies

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Obtain training data and train the model

The project expects the public **Kaggle Flood Risk Prediction Dataset in India** CSV. It is deliberately excluded from the repository.

```powershell
python scripts/download_dataset.py
python scripts/train_model.py
```

If Kaggle is unavailable, place `flood_risk_dataset_india.csv` in `data/` and run the training command. For a clearly labelled, local smoke test only, use:

```powershell
python scripts/train_model.py --dev-synthetic
```

### 3. Start the dashboard

```powershell
python run.py
```

Open <http://127.0.0.1:8000>. If port 8000 is unavailable on your computer, choose another port:

```powershell
python -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

## Demo flow

Select **DEMO MODE** in the dashboard to run the repeatable scenario:

```text
NORMAL -> MONSOON BUILDUP -> HEAVY RAIN -> UPSTREAM SURGE
-> MULTI-NODE EVENT -> NODE FAILURE -> RECOVERY
```

During recovery, rainfall falls first; soil, discharge, water level, and risk respond with delayed causal behaviour. Alerts belong only to the active simulation run and are cleared by reset or a newly selected manual scenario.

## Repository layout

```text
app/                    FastAPI app, API schemas, and simulation services
frontend/               Static dashboard (HTML, CSS, JavaScript)
scripts/                Dataset acquisition and model training commands
data/README.md          Dataset placement instructions; CSV files are ignored
models/README.md        Generated-model artifact instructions; artifacts are ignored
requirements.txt        Python dependencies
run.py                  Local server entry point
```

## API

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Application and model status |
| `POST /predict` | Random Forest prediction for supplied features |
| `GET /api/simulation/state` | Current canonical snapshot and bounded history |
| `GET /api/simulation/history` | Same authoritative snapshot/history payload |
| `POST /api/simulation/start`, `/pause`, `/reset` | Simulation control |
| `POST /api/simulation/scenario` | Set a manual scenario |
| `POST /api/simulation/demo` | Start deterministic demonstration mode |
| `GET /api/nodes`, `GET /api/alerts` | Current snapshot-derived nodes and alerts |
| `WS /ws/live` | Unified live update stream |

Interactive API documentation is available at `/docs` while the server is running.

## Data and model artifacts

The following are intentionally **not committed**:

- Kaggle CSV data and locally generated smoke-test data.
- Trained `.joblib` model and generated metrics, feature-importance, and dataset-statistics JSON.
- Virtual environments, local configuration files, caches, and logs.

This keeps the repository lightweight and prevents accidentally publishing local data or machine-specific artifacts. Recreate the ignored model artifacts by training locally.

## Limitations and responsible use

- The dataset is synthetic; model metrics are not evidence of real-world predictive reliability.
- Map geography uses real named locations, but all sensor placements are proposed/simulated.
- Prototype thresholds are decision-support thresholds, not government emergency thresholds.
- Field deployment requires validated regional data, calibrated hydrology, verified communications, hardware testing, and authorized emergency-management workflows.
