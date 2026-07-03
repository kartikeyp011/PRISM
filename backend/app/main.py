"""PRISM FastAPI application entry point."""

import asyncio
from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from app.alerts.ws_manager import ws_manager
from app.api.routes import router
from app.contract import WS_EVENTS, WS_PATH
from app.db.init_db import init_db
from app.db.session import dispose_engine
from app.services.ingest_subscriber import start_ingest_subscriber, stop_ingest_subscriber
from app.services.redis_client import close_redis

logger = logging.getLogger(__name__)


def _background_index() -> None:
    from app.rag.index import ensure_indexed

    count = ensure_indexed()
    if count:
        logger.info("RAG knowledge index ready (%d chunks)", count)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception:
        logger.exception("Database initialization failed — ingest endpoints may return 503")
    try:
        await start_ingest_subscriber()
    except Exception:
        logger.exception("Redis ingest subscriber failed to start")
    asyncio.create_task(asyncio.to_thread(_background_index))
    yield
    await stop_ingest_subscriber()
    await close_redis()
    await dispose_engine()


app = FastAPI(
    title="PRISM API",
    description="Predictive Risk & Incident Safety Management System",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.websocket(WS_PATH)
async def alerts_websocket(websocket: WebSocket):
    """Real-time alert and risk event channel."""
    await ws_manager.connect(websocket)
    try:
        await websocket.send_json({
            "event": "connected",
            "message": "PRISM alerts channel ready",
            "supported_events": WS_EVENTS,
        })
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception:
        ws_manager.disconnect(websocket)
