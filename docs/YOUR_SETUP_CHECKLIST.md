# PRISM — Your Setup Checklist

Everything below is **your** side of the work. The codebase is ready through **Feature 2** (ingestion + risk alerts).

---

## What you do **NOT** need to install or configure

Docker Compose runs everything for you. **Do not** separately install or set up:

| Service | You do NOT need to… |
|---|---|
| PostgreSQL | Install Postgres, create databases, or run migrations by hand |
| PostGIS / TimescaleDB | Install extensions manually — the Docker image includes them |
| Redis | Install or configure Redis — starts automatically in Docker |
| ChromaDB | Install or configure — container starts with the stack (used later for RAG) |
| Python / Node | Install on your host for normal demo use — runs inside containers |
| Backend / Frontend | Build or deploy manually — `docker compose` handles it |

The backend **auto-creates tables and demo seed data** on first startup. No `psql`, no Redis CLI, no migration commands required.

**You only install one thing:** [Docker Desktop](https://www.docker.com/products/docker-desktop/). Then run two commands (see TL;DR at the bottom).

---

## 1. Install prerequisites (one-time)

| Tool | Required? | Notes |
|---|---|---|
| [Docker Desktop](https://www.docker.com/products/docker-desktop/) | **Yes — the only required install** | Postgres, Redis, Chroma, backend, and frontend all run as containers |
| Git | Recommended | Clone/pull the repo, commit when ready |
| Python 3.11+ | Optional | Only if running backend tests **outside** Docker |
| Node.js 20+ | Optional | Only if running frontend tests **outside** Docker |

After installing Docker Desktop:

- [ ] Start Docker Desktop and wait until it shows **Running**
- [ ] Open PowerShell in the project folder and confirm:

```powershell
docker --version
docker compose version
```

---

## 2. `.env` file — do you need to fill in values?

**No.** For Features 1–2 (ingestion + alerts), copy `.env.example` to `.env` and **leave everything as-is**. You do not need to sign up for anything or look up URLs/passwords.

You already have a `.env` — **you are done with this step.**

| Variable | Change it? | Where the value comes from |
|---|---|---|
| `LLM_BASE_URL` | **Leave empty** | Empty = mock LLM mode (works for RAG demo). Set ngrok URL for live answers. |
| `LLM_MODEL` | No | Default `llama3.2` — only matters when you add Kaggle |
| `DATABASE_URL` | No | Pre-set for Docker internal network (`postgres` hostname) |
| `REDIS_URL` | No | Pre-set for Docker (`redis` hostname) |
| `CHROMA_URL` | No | Pre-set for Docker (`chroma` hostname) — RAG indexes on backend startup |
| `POSTGRES_USER` / `PASSWORD` / `DB` | No | Demo defaults (`prism` / `prism` / `prism`) — Docker Compose creates this automatically |

These are **not secrets you fetch from a website** — they are wiring between containers on the same Docker network. The repo ships working defaults.

### Optional — Live LLM via Kaggle

If you want **live** LLM answers instead of mock mode in the Incidents chat:

1. Run the Kaggle notebook (see [`kaggle/README.md`](../kaggle/README.md))
2. Copy the printed ngrok URL into `LLM_BASE_URL`
3. Restart backend: `docker compose up -d backend`

Until then, **ignore `LLM_BASE_URL`.**

### One-time copy (if you don't have `.env` yet)

```powershell
Copy-Item .env.example .env
```

- [ ] **Do not commit `.env`** — it is already in `.gitignore`

Default ports (only change if something on your PC already uses them):

| Service | Port |
|---|---|
| Backend API | 8000 |
| Frontend | 5173 |
| Postgres | 5432 |
| Redis | 6379 |
| ChromaDB | 8001 |

---

## 3. First run — start the stack

- [ ] Build and start all core services:

```powershell
docker compose up --build
```

First build may take several minutes (downloads images, installs npm/pip deps).

- [ ] Wait until logs show the backend health check passing
- [ ] Open in your browser:
  - Dashboard: http://localhost:5173
  - API docs: http://localhost:8000/docs
  - Health check: http://localhost:8000/api/v1/health

Expected on the dashboard:

- **System Status** — `status: ok`, `llm_mode: mock` (unless you configured LLM)
- **Ingestion Status** — event counts (0 until simulator runs)
- **Alerts** — empty until simulator runs

---

## 4. Run the demo scenario (Features 1 + 2)

With the stack still running, open a **second terminal** in the repo root:

- [ ] Run the simulator:

```powershell
docker compose --profile demo up simulator
```

This replays `compound_risk_demo` — gas readings, hot-work permit, worker entry.

- [ ] Watch the dashboard at http://localhost:5173
- [ ] After batch 3 (~4–6 seconds), you should see:
  - **Ingestion Status** — events ingested count increases
  - **Alerts** — a **HotWorkGasSpike** alert (HIGH severity)
  - Toast appears via WebSocket (no page refresh needed)

- [ ] Click **Acknowledge** on an alert — it should disappear from the active list

### Quick API checks (optional)

```powershell
curl http://localhost:8000/api/v1/sensors/latest
curl http://localhost:8000/api/v1/alerts/active
curl http://localhost:8000/api/v1/risk/active
```

---

## 4b. Try Incident Intelligence (Feature 4)

With the stack running:

- [ ] Open http://localhost:5173 and click **Incidents** in the nav
- [ ] Ask: "What are the hot work permit requirements?"
- [ ] Confirm the answer includes **sources** (SOP citations) and related context
- [ ] Try: "What is the minimum oxygen level for confined space entry?"

Optional API check:

```powershell
curl -X POST http://localhost:8000/api/v1/rag/query -H "Content-Type: application/json" -d "{\"query\":\"hot work permit requirements\"}"
```

First backend start may take 1–2 minutes while embeddings index into ChromaDB.

---

## 5. Run tests (optional but recommended)

### Backend unit tests (no Docker required)

```powershell
cd backend
pip install -r requirements.txt
pytest
python scripts/validate_contract.py
```

Expected: all unit tests pass; integration tests **skipped** (that is normal).

### Backend integration tests (Docker must be running)

With `docker compose up` running postgres + redis + backend:

```powershell
cd backend
$env:INTEGRATION_TESTS = "1"
$env:DATABASE_URL = "postgresql+asyncpg://prism:prism@localhost:5432/prism"
$env:REDIS_URL = "redis://localhost:6379/0"
pytest -m integration
```

- [ ] Integration tests pass (ingestion, risk alerts, WebSocket)

### Frontend tests

```powershell
cd frontend
npm install
npm test
```

---

## 6. Git commits (when you are ready)

The agent does **not** commit for you unless you ask. Suggested commits so far:

```text
docs: add phase 0 architecture and user flow diagrams
feat: scaffold repo, api contract, and kaggle llm bridge
feat: add simulator ingestion and time-series storage
feat: add compound risk engine and realtime alerts
feat: add geospatial safety map and operations dashboard
feat: add rag compliance and incident intelligence
```

- [ ] Review changes: `git status`
- [ ] Stage and commit when satisfied

---

## 7. Optional — Live LLM via Kaggle

The Incidents page works out of the box with **mock LLM mode** when `LLM_BASE_URL` is empty. For richer, live-generated answers:

- [ ] Create a [Kaggle](https://www.kaggle.com/) account (GPU quota)
- [ ] Create an [ngrok](https://ngrok.com/) account and copy your authtoken
- [ ] Add Kaggle secret: `NGROK_AUTH_TOKEN`
- [ ] Upload and run [`kaggle/ollama_ngrok_server.ipynb`](../kaggle/ollama_ngrok_server.ipynb) with **GPU + Internet** enabled
- [ ] Copy the printed ngrok URL into `.env`:

```env
LLM_BASE_URL=https://xxxx.ngrok-free.app
LLM_MODEL=llama3.2
```

- [ ] Restart backend: `docker compose up -d backend`

Full details: [`kaggle/README.md`](../kaggle/README.md)

**Note:** ngrok free URLs change every time you restart the notebook. Update `.env` each time.

---

## 8. Not needed yet (future features)

| Item | When |
|---|---|
| CCTV / computer vision | Optional phase |
| Production deployment | Out of scope for prototype |

First backend startup may take 1–2 minutes while the embedding model downloads and knowledge docs index into ChromaDB.

---

## 9. Troubleshooting

### `docker` is not recognized

Install [Docker Desktop for Windows](https://www.docker.com/products/docker-desktop/) and restart your terminal.

### Backend returns 503 on ingest

Postgres may still be starting. Wait 30–60 seconds and retry. Check logs:

```powershell
docker compose logs backend postgres
```

### Dashboard shows "API unreachable"

- Confirm backend is up: http://localhost:8000/api/v1/health
- Restart frontend: `docker compose up -d frontend`

### Alerts do not appear after simulator

- Confirm simulator finished without errors: `docker compose logs simulator`
- Check active alerts: http://localhost:8000/api/v1/alerts/active
- Re-run simulator (duplicate events are skipped — reset DB if needed):

```powershell
docker compose down -v
docker compose up --build
docker compose --profile demo up simulator
```

### WebSocket alerts not showing live

- Hard-refresh the dashboard (Ctrl+F5)
- Alerts still appear on the 8-second poll even if WebSocket fails
- Check browser console for WebSocket errors to `ws://localhost:8000/ws/alerts`

### Port already in use

Stop conflicting services or change ports in `docker-compose.yml`.

---

## 10. Minimum checklist (TL;DR)

**Install Docker Desktop only.** Everything else is automatic.

1. [ ] Install and start **Docker Desktop**
2. [ ] `Copy-Item .env.example .env` (skip if you already have `.env`)
3. [ ] `docker compose up --build` — starts Postgres, Redis, Chroma, backend, frontend
4. [ ] Open http://localhost:5173
5. [ ] `docker compose --profile demo up simulator` — confirm **HotWorkGasSpike** alert appears
6. [ ] Open **Incidents** — ask a compliance question and confirm cited sources

No separate Postgres, Redis, or database setup. Kaggle/ngrok is optional for live LLM answers.

---

## Document history

| Date | Notes |
|---|---|
| 2026-07-03 | Created after Feature 2 completion |
