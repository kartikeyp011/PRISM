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

### 1. Clone and configure

```bash
cp .env.example .env
# Edit .env — leave LLM_BASE_URL empty for mock mode
```

### 2. Start services

```bash
docker compose up --build
```

- Backend API: http://localhost:8000
- Frontend: http://localhost:5173
- API docs: http://localhost:8000/docs

### 3. Optional — Live LLM via Kaggle

See [`kaggle/README.md`](kaggle/README.md) for running the Ollama + ngrok notebook, then set `LLM_BASE_URL` in `.env`.

### 4. Run tests

```bash
cd backend
pip install -r requirements.txt
pytest
python scripts/validate_contract.py
```

## API Contract

Single source of truth: [`backend/api_contract.yaml`](backend/api_contract.yaml)

All endpoints, constants, Redis topics, and WebSocket events are defined there.

## Status

**Phase 1 complete** — API contract, Docker Compose scaffold, stub endpoints, Kaggle LLM bridge, mock LLM client.

| Component | Status |
|---|---|
| Architecture docs | Done (Phase 0) |
| API contract + validator | Done |
| Docker Compose (postgres, redis, chroma, backend, frontend) | Done |
| Stub REST endpoints + WebSocket | Done |
| Kaggle Ollama/ngrok notebook | Done |
| LLM client (mock + live) | Done |
| Feature 1: Ingestion + simulator | Planned |

## Project Docs

- [`docs/architecture.md`](docs/architecture.md)
- [`docs/user-flows/`](docs/user-flows/)
