"""Redis subscriber for async ingest-triggered risk re-evaluation."""

from __future__ import annotations

import asyncio
import json
import logging

from app.contract import REDIS_TOPIC_EVENTS_INGEST
from app.db.session import AsyncSessionLocal
from app.risk.engine import evaluate_zones
from app.services.redis_client import get_redis

logger = logging.getLogger(__name__)

_subscriber_task: asyncio.Task | None = None


async def _handle_message(payload: dict) -> None:
    zone_ids = payload.get("zone_ids", [])
    if not zone_ids:
        return
    async with AsyncSessionLocal() as session:
        try:
            await evaluate_zones(session, zone_ids)
            await session.commit()
        except Exception:
            await session.rollback()
            logger.exception("Async risk re-evaluation failed")


async def _subscribe_loop() -> None:
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(REDIS_TOPIC_EVENTS_INGEST)
    logger.info("Subscribed to %s", REDIS_TOPIC_EVENTS_INGEST)
    async for message in pubsub.listen():
        if message["type"] != "message":
            continue
        try:
            payload = json.loads(message["data"])
            await _handle_message(payload)
        except Exception:
            logger.exception("Failed to process ingest pub/sub message")


async def start_ingest_subscriber() -> None:
    global _subscriber_task
    if _subscriber_task is not None:
        return
    _subscriber_task = asyncio.create_task(_subscribe_loop())


async def stop_ingest_subscriber() -> None:
    global _subscriber_task
    if _subscriber_task is not None:
        _subscriber_task.cancel()
        try:
            await _subscriber_task
        except asyncio.CancelledError:
            pass
        _subscriber_task = None
