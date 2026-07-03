"""API route handlers."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.alerts import alert_agent
from app.agents.ingestion import ingestion_agent
from app.agents.risk import risk_agent
from app.config import settings
from app.contract import (
    PATH_ALERTS_ACK,
    PATH_ALERTS_ACTIVE,
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
from app.db.session import get_session
from app.models.schemas import (
    AlertAckRequest,
    AlertAckResponse,
    AlertItem,
    AlertsActiveResponse,
    HealthResponse,
    IngestEventsRequest,
    IngestEventsResponse,
    MapLayersResponse,
    RagQueryRequest,
    RagQueryResponse,
    RagSource,
    RiskActiveResponse,
    RiskAssessment,
    SensorReading,
    SensorsLatestResponse,
    validate_event_type,
)
from app.map.service import build_map_layers

router = APIRouter()
CONTRACT_VERSION = "1.0.0"

PUBSUB_TOPICS = {
    "ingest": REDIS_TOPIC_EVENTS_INGEST,
    "alerts": REDIS_TOPIC_ALERTS,
    "risk": REDIS_TOPIC_RISK,
}
WS_EVENT_NAMES = WS_EVENTS


@router.get(PATH_HEALTH, response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=CONTRACT_VERSION,
        llm_mode=settings.llm_mode,
    )


@router.post(PATH_INGEST_EVENTS, response_model=IngestEventsResponse)
async def ingest_events(
    body: IngestEventsRequest,
    response: Response,
    session: AsyncSession = Depends(get_session),
) -> IngestEventsResponse:
    for event in body.events:
        if not validate_event_type(event.event_type):
            raise HTTPException(
                status_code=400,
                detail=f"Invalid event_type: {event.event_type}",
            )

    try:
        result = await ingestion_agent.process_batch(session, body.events)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc

    if result.accepted == 0 and result.skipped > 0:
        response.status_code = 200
    else:
        response.status_code = 202

    return IngestEventsResponse(
        accepted=result.accepted,
        skipped=result.skipped,
        event_ids=result.event_ids,
        status=result.status,
    )


@router.get(PATH_SENSORS_LATEST, response_model=SensorsLatestResponse)
async def sensors_latest(
    zone_id: str | None = None,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
) -> SensorsLatestResponse:
    try:
        rows, count, last_event_at, events_ingested = await ingestion_agent.latest_sensors(
            session, zone_id=zone_id, limit=limit
        )
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc

    readings = [SensorReading(**row) for row in rows]
    return SensorsLatestResponse(
        readings=readings,
        count=count,
        events_ingested=events_ingested,
        last_event_at=last_event_at,
    )


@router.get(PATH_RISK_ACTIVE, response_model=RiskActiveResponse)
async def risk_active(
    zone_id: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> RiskActiveResponse:
    try:
        records = await risk_agent.get_active_assessments(session, zone_id=zone_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc

    assessments = [
        RiskAssessment(
            assessment_id=str(r.id),
            zone_id=str(r.zone_id),
            rule_id=r.rule_id,
            risk_level=r.risk_level,
            assessed_at=r.assessed_at.isoformat(),
            context=r.context,
        )
        for r in records
    ]
    return RiskActiveResponse(assessments=assessments, count=len(assessments))


@router.get(PATH_ALERTS_ACTIVE, response_model=AlertsActiveResponse)
async def alerts_active(
    zone_id: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> AlertsActiveResponse:
    try:
        alerts = await alert_agent.list_active(session, zone_id=zone_id)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc

    items = [
        AlertItem(
            alert_id=str(a.id),
            zone_id=str(a.zone_id),
            rule_id=a.rule_id,
            severity=a.severity,
            status=a.status,
            message=a.message,
            created_at=a.created_at.isoformat(),
        )
        for a in alerts
    ]
    return AlertsActiveResponse(alerts=items, count=len(items))


@router.post(PATH_ALERTS_ACK, response_model=AlertAckResponse)
async def alerts_ack(
    body: AlertAckRequest,
    session: AsyncSession = Depends(get_session),
) -> AlertAckResponse:
    try:
        alert = await alert_agent.acknowledge(
            session, body.alert_id, body.acknowledged_by
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc

    return AlertAckResponse(alert_id=str(alert.id), status=alert.status)


@router.get(PATH_MAP_LAYERS, response_model=MapLayersResponse)
async def map_layers(session: AsyncSession = Depends(get_session)) -> MapLayersResponse:
    try:
        data = await build_map_layers(session)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Database unavailable: {exc}") from exc
    return MapLayersResponse(**data)


@router.post(PATH_RAG_QUERY, response_model=RagQueryResponse)
async def rag_query(body: RagQueryRequest) -> RagQueryResponse:
    from app.services.llm_client import ChatMessage, llm_client
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
