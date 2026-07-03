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

### Demo simulator + alerts (Features 1–2)

```bash
docker compose --profile demo up simulator
```

Replays `compound_risk_demo` — when LEL exceeds 15% with an active hot-work permit, a **HotWorkGasSpike** alert appears on the dashboard via WebSocket.

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

**Feature 2 complete** — compound risk engine and realtime alerts.

| Component | Status |
|---|---|
| Simulator + ingestion + TimescaleDB | Done |
| **Risk engine + alerts + WebSocket** | **Done** |
| Geospatial map | Planned |
| RAG compliance | Planned |

## Project Docs

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/user-flows/`](docs/user-flows/)
