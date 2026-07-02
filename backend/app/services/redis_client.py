"""Redis pub/sub client."""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from app.config import settings

logger = logging.getLogger(__name__)

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


async def publish(topic: str, payload: dict[str, Any]) -> None:
    try:
        client = await get_redis()
        await client.publish(topic, json.dumps(payload))
    except Exception:
        logger.exception("Failed to publish to Redis topic %s", topic)
