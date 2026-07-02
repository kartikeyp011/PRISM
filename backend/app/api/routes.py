"""API route handlers — stub implementations for Phase 1."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.config import settings
from app.contract import (
    PATH_ALERTS_ACK,
    PATH_HEALTH,
    PATH_INGEST_EVENTS,
    PATH_MAP_LAYERS,
    PATH_RAG_QUERY,
    PATH_RISK_ACTIVE,
    PATH_SENSORS_LATEST,
    REDIS_TOPIC_ALERTS,
    REDIS_TOPIC_EVENTS_INGEST,
    REDIS_TOPIC_RISK,
    WS_EVENTS,
)
from app.models.schemas import (
    AlertAckRequest,
    AlertAckResponse,
    HealthResponse,
    IngestEventsRequest,
    IngestEventsResponse,
    MapLayersResponse,
    RagQueryRequest,
    RagQueryResponse,
    RagSource,
    RiskActiveResponse,
    SensorsLatestResponse,
    validate_event_type,
)
from app.services.llm_client import ChatMessage, llm_client

router = APIRouter()
CONTRACT_VERSION = "1.0.0"

# Contract-aligned pub/sub and WebSocket event names (used by Features 2+)
PUBSUB_TOPICS = {
    "ingest": REDIS_TOPIC_EVENTS_INGEST,
    "alerts": REDIS_TOPIC_ALERTS,
    "risk": REDIS_TOPIC_RISK,
}
WS_EVENT_NAMES = WS_EVENTS  # alert.created, alert.updated, risk.changed


@router.get(PATH_HEALTH, response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=CONTRACT_VERSION,
        llm_mode=settings.llm_mode,
    )


@router.post(PATH_INGEST_EVENTS, response_model=IngestEventsResponse, status_code=202)
async def ingest_events(body: IngestEventsRequest) -> IngestEventsResponse:
    for event in body.events:
        if not validate_event_type(event.event_type):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event_type: {event.event_type}",
            )
    event_ids = [e.event_id for e in body.events]
    return IngestEventsResponse(accepted=len(event_ids), event_ids=event_ids)


@router.get(PATH_SENSORS_LATEST, response_model=SensorsLatestResponse)
async def sensors_latest(zone_id: str | None = None, limit: int = 50) -> SensorsLatestResponse:
    return SensorsLatestResponse(readings=[], count=0, last_event_at=None)


@router.get(PATH_RISK_ACTIVE, response_model=RiskActiveResponse)
async def risk_active(zone_id: str | None = None) -> RiskActiveResponse:
    return RiskActiveResponse(assessments=[], count=0)


@router.post(PATH_ALERTS_ACK, response_model=AlertAckResponse)
async def alerts_ack(body: AlertAckRequest) -> AlertAckResponse:
    return AlertAckResponse(alert_id=body.alert_id, status="ACKNOWLEDGED")


@router.get(PATH_MAP_LAYERS, response_model=MapLayersResponse)
async def map_layers() -> MapLayersResponse:
    empty_fc = {"type": "FeatureCollection", "features": []}
    return MapLayersResponse(
        layers={
            "zones": empty_fc,
            "sensors": empty_fc,
            "workers": empty_fc,
            "permits": empty_fc,
        }
    )


@router.post(PATH_RAG_QUERY, response_model=RagQueryResponse)
async def rag_query(body: RagQueryRequest) -> RagQueryResponse:
    session_id = body.session_id or str(uuid.uuid4())
    result = await llm_client.chat(
        [
            ChatMessage(role="system", content="You are a safety compliance assistant."),
            ChatMessage(role="user", content=body.query),
        ]
    )
    sources = [
        RagSource(
            document_id="mock-sop-hot-work",
            title="Hot Work Permit SOP",
            excerpt="Gas monitoring and fire watch required before hot work.",
            score=0.92,
        )
    ] if llm_client.is_mock else []
    return RagQueryResponse(
        answer=result.content,
        sources=sources,
        session_id=session_id,
        llm_mode=result.mode,
    )
