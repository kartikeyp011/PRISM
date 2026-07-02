# PRISM

**Predictive Risk & Incident Safety Management System** — a multi-agent AI platform for zero-harm operations in heavy industrial facilities.

## Tech Stack

- **Backend:** Python 3.12, FastAPI
- **Database:** PostgreSQL 16 + PostGIS + TimescaleDB
- **Cache:** Redis 7
- **Vector store:** ChromaDB
- **Frontend:** React 18, TypeScript, Vite
- **Map:** Leaflet + OpenStreetMap
- **LLM:** Ollama on Kaggle, exposed via ngrok
- **Orchestration:** Docker Compose

## Setup

```bash
cp .env.example .env
docker compose up --build
```

- Backend API: http://localhost:8000
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

### Demo simulator (Feature 1)

```bash
docker compose --profile demo up simulator
```

Replays `compound_risk_demo` — LEL gas readings, hot-work permit, worker entry in confined zone A.

### Optional — Live LLM via Kaggle

See [`kaggle/README.md`](kaggle/README.md), then set `LLM_BASE_URL` in `.env`.

## Tests

```bash
# Backend unit tests
cd backend
pip install -r requirements.txt
pytest

# Integration tests (postgres + redis required)
INTEGRATION_TESTS=1 DATABASE_URL=postgresql+asyncpg://prism:prism@localhost:5432/prism pytest -m integration

# Frontend
cd frontend
npm install
npm test
```

## API Contract

Single source of truth: [`backend/api_contract.yaml`](backend/api_contract.yaml)

## Status

**Feature 1 complete** — simulator ingestion and time-series storage.

| Component | Status |
|---|---|
| Architecture docs | Done |
| API contract + validator | Done |
| Docker Compose scaffold | Done |
| **Simulator + ingestion + TimescaleDB** | **Done** |
| Risk engine + alerts | Planned |
| Geospatial map | Planned |
| RAG compliance | Planned |

## Project Docs

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/user-flows/`](docs/user-flows/)
