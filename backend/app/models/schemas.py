"""Pydantic schemas aligned with api_contract.yaml."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.contract import ALERT_STATUSES, EVENT_TYPES, RISK_LEVELS


class HealthResponse(BaseModel):
    status: str
    version: str
    llm_mode: str


class IngestEventItem(BaseModel):
    event_id: str
    event_type: str
    timestamp: str
    zone_id: str
    payload: dict[str, Any] = Field(default_factory=dict)


class IngestEventsRequest(BaseModel):
    events: list[IngestEventItem]


class IngestEventsResponse(BaseModel):
    accepted: int
    skipped: int = 0
    event_ids: list[str]
    status: str = "accepted"


class SensorReading(BaseModel):
    sensor_id: str
    zone_id: str
    sensor_type: str
    value: float
    unit: str
    timestamp: str


class SensorsLatestResponse(BaseModel):
    readings: list[SensorReading]
    count: int
    events_ingested: int = 0
    last_event_at: str | None = None


class RiskAssessment(BaseModel):
    assessment_id: str
    zone_id: str
    rule_id: str
    risk_level: str
    assessed_at: str
    context: dict[str, Any] = Field(default_factory=dict)


class RiskActiveResponse(BaseModel):
    assessments: list[RiskAssessment]
    count: int


class AlertAckRequest(BaseModel):
    alert_id: str
    acknowledged_by: str | None = None


class AlertAckResponse(BaseModel):
    alert_id: str
    status: str


class AlertItem(BaseModel):
    alert_id: str
    zone_id: str
    rule_id: str
    severity: str
    status: str
    message: str
    created_at: str


class AlertsActiveResponse(BaseModel):
    alerts: list[AlertItem]
    count: int


class MapLayersResponse(BaseModel):
    type: str = "FeatureCollection"
    layers: dict[str, Any]


class RagSource(BaseModel):
    document_id: str
    title: str
    excerpt: str
    score: float


class RagQueryRequest(BaseModel):
    query: str
    session_id: str | None = None
    top_k: int = 5


class RagQueryResponse(BaseModel):
    answer: str
    sources: list[RagSource]
    session_id: str
    llm_mode: str


def validate_event_type(value: str) -> bool:
    return value in EVENT_TYPES


def validate_risk_level(value: str) -> bool:
    return value in RISK_LEVELS


def validate_alert_status(value: str) -> bool:
    return value in ALERT_STATUSES
