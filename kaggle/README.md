# PRISM — Kaggle Ollama + ngrok LLM Server

Expose an Ollama API from a Kaggle GPU notebook via ngrok so the local PRISM backend can call it for RAG chat completions.

## Prerequisites

1. [Kaggle account](https://www.kaggle.com/) with GPU quota
2. [ngrok account](https://ngrok.com/) and auth token
3. Local PRISM repo cloned

## Step 1: Add Kaggle Secrets

In Kaggle → **Account** → **Create New Secret**:

| Secret name | Value |
|---|---|
| `NGROK_AUTH_TOKEN` | Your ngrok authtoken from [dashboard.ngrok.com](https://dashboard.ngrok.com/get-started/your-authtoken) |

## Step 2: Upload and Run the Notebook

1. Open [Kaggle Notebooks](https://www.kaggle.com/code)
2. Click **New Notebook**
3. Upload `ollama_ngrok_server.ipynb` or copy its cells
4. Enable **GPU** (Settings → Accelerator → GPU T4 x2 or P100)
5. Enable **Internet** (Settings → Internet → On)
6. Run all cells

The notebook will:

1. Install Ollama on the Kaggle Linux environment
2. Pull a small model (`llama3.2:3b`)
3. Start Ollama on port `11434`
4. Start an ngrok tunnel to expose the API publicly
5. Print the public URL and verify with `/api/tags`

## Step 3: Copy ngrok URL to Local `.env`

When the notebook prints something like:

```
Public Ollama URL: https://abcd-1234.ngrok-free.app
```

Copy that URL into your local PRISM `.env`:

```env
LLM_BASE_URL=https://abcd-1234.ngrok-free.app
LLM_MODEL=llama3.2
```

Then restart the backend:

```bash
docker compose up -d backend
```

Verify from your machine:

```bash
curl https://abcd-1234.ngrok-free.app/api/tags
curl http://localhost:8000/api/v1/health
```

The health endpoint should report `"llm_mode": "live"` once configured.

## Step 4: Test RAG Query

```bash
curl -X POST http://localhost:8000/api/v1/rag/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What are hot work permit requirements?"}'
```

## Troubleshooting

| Issue | Fix |
|---|---|
| ngrok URL changes on restart | Re-run notebook, update `LLM_BASE_URL` in `.env` |
| Kaggle session timeout | Re-run notebook; sessions expire after ~12 hours |
| Model pull fails (disk) | Use `llama3.2:3b` or smaller quantized model |
| ngrok 403 / blocked | Ensure `NGROK_AUTH_TOKEN` secret is set correctly |
| CORS errors | Backend calls ngrok server-side; CORS not needed |

## Mock Mode (No Kaggle)

Leave `LLM_BASE_URL` empty in `.env` for offline development. The backend returns canned RAG answers automatically.

## OpenAI-Compatible Endpoints

Ollama exposes these endpoints through ngrok:

- `GET /api/tags` — list models
- `POST /v1/chat/completions` — chat (used by PRISM RAG)
- `POST /v1/embeddings` — embeddings (optional; PRISM uses local embeddings for indexing)
