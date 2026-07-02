"""PRISM FastAPI application entry point."""

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.contract import WS_EVENTS, WS_PATH
from app.db.init_db import init_db
from app.db.session import dispose_engine
from app.services.redis_client import close_redis

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
        logger.info("Database initialized")
    except Exception:
        logger.exception("Database initialization failed — ingest endpoints may return 503")
    yield
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
async def alerts_websocket(websocket):
    """WebSocket stub — full implementation in Feature 2."""
    await websocket.accept()
    await websocket.send_json({
        "event": "connected",
        "message": "PRISM alerts channel ready",
        "supported_events": WS_EVENTS,
    })
    await websocket.close()
