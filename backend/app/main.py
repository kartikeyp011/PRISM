"""PRISM FastAPI application entry point."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.contract import WS_EVENTS, WS_PATH

app = FastAPI(
    title="PRISM API",
    description="Predictive Risk & Incident Safety Management System",
    version="1.0.0",
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
