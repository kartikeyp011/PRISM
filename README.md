# PRISM

**Predictive Risk & Incident Safety Management System** — a multi-agent AI platform for zero-harm operations in heavy industrial facilities.

## Quick start

```bash
cp .env.example .env
docker compose up --build
```

Open http://localhost:5173

**Full demo walkthrough:** [`docs/DEMO_RUNBOOK.md`](docs/DEMO_RUNBOOK.md)  
**Setup checklist:** [`docs/YOUR_SETUP_CHECKLIST.md`](docs/YOUR_SETUP_CHECKLIST.md)

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.12, FastAPI |
| Database | PostgreSQL 16 + PostGIS + TimescaleDB |
| Cache | Redis 7 |
| Vector store | ChromaDB |
| Frontend | React 18, TypeScript, Vite |
| Map | Leaflet + OpenStreetMap |
| LLM | Ollama on Kaggle via ngrok (mock mode default) |
| CV | YOLOv8 via ultralytics (mock mode default) |
| Orchestration | Docker Compose |
| Testing | pytest, Vitest, Playwright |

## Services

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

## Demo (5 minutes)

```bash
# Terminal 1
docker compose up --build

# Terminal 2 — replay compound risk scenario
docker compose --profile demo up simulator
```

Then on the dashboard:

1. Watch **HotWorkGasSpike** alert appear
2. Open **Safety Map** → run **CCTV Analysis** (Missing PPE sample)
3. Open **Incidents** → ask a hot work SOP question

See [`docs/DEMO_RUNBOOK.md`](docs/DEMO_RUNBOOK.md) for the full presenter script.

## Tests

### Unit tests (no Docker)

```bash
cd backend && pip install -r requirements.txt && pytest -k "not integration"
cd frontend && npm install && npm test
python backend/scripts/validate_contract.py
```

### Integration tests (Docker running)

```powershell
cd backend
$env:INTEGRATION_TESTS = "1"
$env:DATABASE_URL = "postgresql+asyncpg://prism:prism@localhost:5432/prism"
pytest -m integration
```

### Playwright E2E smoke tests

Requires the stack running on :5173 (and :8000 for the RAG happy-path test):

```powershell
cd frontend
npm install
npx playwright install chromium
$env:PLAYWRIGHT_SKIP_WEBSERVER = "1"
npm run test:e2e
```

### All tests (helper script)

```powershell
.\scripts\run_all_tests.ps1                      # unit only
.\scripts\run_all_tests.ps1 -Integration         # + backend integration
.\scripts\run_all_tests.ps1 -Integration -E2E    # + Playwright
```

## API Contract

Single source of truth: [`backend/api_contract.yaml`](backend/api_contract.yaml)

Validate: `python backend/scripts/validate_contract.py`

## Project Status

**Prototype complete** — all planned features implemented and tested.

| Feature | Description | Status |
|---|---|---|
| 1 — Ingestion | Simulator, TimescaleDB, ingest API | Done |
| 2 — Risk + Alerts | Compound rules, WebSocket, alert UI | Done |
| 3 — Safety Map | PostGIS GeoJSON, Leaflet dashboard | Done |
| 4 — RAG | ChromaDB, compliance chat, incidents | Done |
| 5 — CV (optional) | Mock/YOLOv8 CCTV analysis, map overlay | Done |

Mock modes for LLM (`LLM_BASE_URL` empty) and CV (`CV_ENABLED=false`) work without external services.

## Project Docs

- [`docs/architecture.md`](docs/architecture.md) — system design
- [`docs/DEMO_RUNBOOK.md`](docs/DEMO_RUNBOOK.md) — end-to-end demo script
- [`docs/user-flows/`](docs/user-flows/) — per-feature flows
- [`kaggle/README.md`](kaggle/README.md) — optional live LLM setup
