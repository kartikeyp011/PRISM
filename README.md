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

**Manual steps for you:** see [`docs/YOUR_SETUP_CHECKLIST.md`](docs/YOUR_SETUP_CHECKLIST.md)

```bash
cp .env.example .env
docker compose up --build
```

- Backend API: http://localhost:8000
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

### Demo simulator + alerts (Features 1–2)

```bash
docker compose --profile demo up simulator
```

Replays `compound_risk_demo` — alerts fire and the **Safety Map** shows live zones, sensors, workers, and permits.

Open **Dashboard** for ingestion + compact map, or **Safety Map** for full-screen view.

### Optional — Live LLM via Kaggle

See [`kaggle/README.md`](kaggle/README.md), then set `LLM_BASE_URL` in `.env`.

## Tests

```bash
cd backend && pip install -r requirements.txt && pytest
INTEGRATION_TESTS=1 DATABASE_URL=postgresql+asyncpg://prism:prism@localhost:5432/prism pytest -m integration
cd frontend && npm test
```

## API Contract

Single source of truth: [`backend/api_contract.yaml`](backend/api_contract.yaml)

## Status

**Feature 3 complete** — geospatial safety map and operations dashboard.

| Component | Status |
|---|---|
| Simulator + ingestion + TimescaleDB | Done |
| Risk engine + alerts + WebSocket | Done |
| **Geospatial map + dashboard UI** | **Done** |
| RAG compliance | Planned |

## Project Docs

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/user-flows/`](docs/user-flows/)
