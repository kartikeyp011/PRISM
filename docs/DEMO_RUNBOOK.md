# PRISM — End-to-End Demo Runbook

Step-by-step guide to run the full PRISM prototype demo locally.

**Time:** ~10 minutes (first run may take longer for Docker image pulls and RAG indexing)

---

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- `.env` file in repo root (copy from `.env.example` if needed)

No Kaggle, ngrok, or GPU required — mock LLM and mock CV work out of the box.

---

## Step 1 — Start the stack

From the repo root:

```powershell
docker compose up --build
```

Wait until all services are healthy. First backend start may take 1–2 minutes while knowledge docs index into ChromaDB.

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API | http://localhost:8000 |
| API docs | http://localhost:8000/docs |

Open http://localhost:5173 — you should see the **Dashboard** with System Status and a compact Safety Map.

---

## Step 2 — Run the compound risk demo

Open a **second terminal** in the repo root:

```powershell
docker compose --profile demo up simulator
```

This replays `compound_risk_demo` — gas readings, hot-work permit, worker entry.

### Expected results (~5 seconds)

| Area | What to look for |
|---|---|
| **Dashboard → Ingestion Status** | Events ingested count increases |
| **Alert strip** (top) | **HotWorkGasSpike** alert appears (HIGH) |
| **Safety Map** | Zone polygon colored by risk level; sensor markers update |
| **WebSocket** | Alert toast appears without page refresh |

### Optional API checks

```powershell
curl http://localhost:8000/api/v1/alerts/active
curl http://localhost:8000/api/v1/sensors/latest
curl http://localhost:8000/api/v1/risk/active
```

---

## Step 3 — Acknowledge an alert

1. Click **Acknowledge** on the alert in the alert strip or Alerts panel
2. Alert should disappear from the active list

---

## Step 4 — Explore the Safety Map

1. Click **Safety Map** in the nav
2. Toggle layers: zones, sensors, workers, permits, **cameras**
3. Click a zone polygon → detail drawer shows risk level and linked alerts
4. Click a sensor marker → latest reading and status

---

## Step 5 — CCTV analysis (Feature 5)

On the **Safety Map** page:

1. Scroll to **CCTV Analysis**
2. Select **Missing PPE** from the demo sample dropdown
3. Click **Analyze frame**

### Expected results

- Detections list shows `no_hard_hat`, `no_safety_vest`
- Hazards section shows **PPE_VIOLATION**
- Camera marker on map turns **orange** (warning)
- Click the camera marker → drawer shows CV hazards

---

## Step 6 — Incident Intelligence (RAG)

1. Click **Incidents** in the nav
2. Click an example question or type:

   > What are the hot work permit requirements before starting welding?

3. Wait for the response (mock LLM mode when `LLM_BASE_URL` is empty)

### Expected results

- Answer text with compliance guidance
- **Sources** section with SOP citations (e.g. `sop-hot-work-001`)
- LLM mode shown as **mock**

Try also:

> What is the minimum oxygen level for confined space entry?

---

## Step 7 — Optional live LLM (Kaggle + ngrok)

Only if you want live-generated answers instead of mock mode:

1. Follow [`kaggle/README.md`](../kaggle/README.md)
2. Set `LLM_BASE_URL` in `.env` to your ngrok URL
3. Restart backend: `docker compose up -d backend`
4. Repeat Step 6 — LLM mode should show **live**

---

## Step 8 — Optional live CV (YOLOv8)

Only if you want live object detection instead of mock CV:

1. Set in `.env`:

   ```env
   CV_ENABLED=true
   CV_MODEL=yolov8n.pt
   ```

2. Rebuild backend: `docker compose up -d --build backend`
3. Repeat Step 5 — `cv_mode` in response should show **live**

---

## Demo script (presenter checklist)

Use this order for a live walkthrough:

1. [ ] Show Dashboard — explain ingestion + map overview
2. [ ] Run simulator — narrate IoT events hitting the API
3. [ ] Point out **HotWorkGasSpike** alert (compound rule: hot work + LEL spike)
4. [ ] Acknowledge alert
5. [ ] Open Safety Map — show geospatial layers
6. [ ] Run CCTV **Missing PPE** analysis — show hazard overlay
7. [ ] Open Incidents — ask hot work SOP question — show cited sources
8. [ ] (Optional) Mention live LLM/CV via `.env` for production-like mode

---

## Troubleshooting

| Issue | Fix |
|---|---|
| Backend unhealthy on first start | Wait 1–2 min for RAG indexing; check `docker compose logs backend` |
| No alerts after simulator | Ensure simulator finished batch 3; check `curl .../alerts/active` |
| RAG returns empty sources | Run `docker compose exec backend python -m app.rag.index` |
| Map empty | Simulator must run at least once; zones are seeded on DB init |
| E2E tests fail | Ensure stack is up on :5173 and :8000 for full RAG test |

---

## Running automated tests

See [`README.md`](../README.md#tests) for unit, integration, and Playwright commands.

Quick smoke (no Docker):

```powershell
cd backend; pytest -k "not integration"
cd frontend; npm test
```

Full suite (Docker must be running):

```powershell
cd backend
$env:INTEGRATION_TESTS = "1"
$env:DATABASE_URL = "postgresql+asyncpg://prism:prism@localhost:5432/prism"
pytest

cd ../frontend
$env:PLAYWRIGHT_SKIP_WEBSERVER = "1"
npm run test:e2e
```

Or use the helper script: `.\scripts\run_all_tests.ps1`

---

## Document history

| Date | Notes |
|---|---|
| 2026-07-03 | Created for Phase 7 finalize |
