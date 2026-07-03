"""RAG query orchestration."""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Alert, Incident
from app.rag.retriever import RetrievedChunk, retrieve
from app.services.llm_client import ChatMessage, llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are PRISM compliance assistant for industrial safety. "
    "Answer using ONLY the provided context. Cite document IDs when relevant. "
    "If context is insufficient, say so clearly."
)


@dataclass
class RagResult:
    answer: str
    sources: list[RetrievedChunk]
    session_id: str
    llm_mode: str
    related_alerts: list[dict]
    related_incidents: list[dict]


def _build_context(chunks: list[RetrievedChunk]) -> str:
    parts = []
    for i, chunk in enumerate(chunks, start=1):
        parts.append(
            f"[Source {i}] {chunk.title} ({chunk.document_id})\n{chunk.excerpt}"
        )
    return "\n\n".join(parts)


async def _related_alerts(session: AsyncSession, query: str) -> list[dict]:
    result = await session.execute(
        select(Alert).where(Alert.status == "ACTIVE").order_by(Alert.created_at.desc()).limit(10)
    )
    alerts = list(result.scalars().all())
    query_lower = query.lower()
    related = []
    for alert in alerts:
        if any(
            kw in query_lower
            for kw in ("gas", "hot work", "lel", "spike", "confined", "alert", "risk")
        ) or alert.rule_id.lower() in query_lower:
            related.append(
                {
                    "alert_id": str(alert.id),
                    "rule_id": alert.rule_id,
                    "severity": alert.severity,
                    "message": alert.message,
                }
            )
    return related[:5]


async def _related_incidents(session: AsyncSession, query: str) -> list[dict]:
    result = await session.execute(select(Incident).order_by(Incident.occurred_at.desc()).limit(10))
    incidents = list(result.scalars().all())
    query_lower = query.lower()
    related = []
    for inc in incidents:
        title_lower = inc.title.lower()
        if any(kw in query_lower for kw in title_lower.split()) or any(
            kw in query_lower for kw in ("incident", "gas", "spike", "compound")
        ):
            related.append(
                {
                    "incident_id": str(inc.id),
                    "title": inc.title,
                    "status": inc.status,
                    "occurred_at": inc.occurred_at.isoformat(),
                }
            )
    return related[:5]


async def query_rag(
    session: AsyncSession,
    query: str,
    session_id: str | None = None,
    top_k: int = 5,
) -> RagResult:
    sid = session_id or str(uuid.uuid4())
    chunks = retrieve(query, top_k=top_k)

    if not chunks:
        return RagResult(
            answer="No relevant knowledge documents found. Run `python -m app.rag.index` to index seed docs.",
            sources=[],
            session_id=sid,
            llm_mode=llm_client.mode,
            related_alerts=await _related_alerts(session, query),
            related_incidents=await _related_incidents(session, query),
        )

    context = _build_context(chunks)
    user_prompt = f"Context:\n{context}\n\nQuestion: {query}"

    try:
        chat_result = await llm_client.chat(
            [
                ChatMessage(role="system", content=SYSTEM_PROMPT),
                ChatMessage(role="user", content=user_prompt),
            ]
        )
        answer = chat_result.content
        mode = chat_result.mode
    except Exception:
        logger.exception("LLM generation failed")
        answer = (
            "Retrieved relevant sources but LLM generation failed. "
            "Top excerpt: " + chunks[0].excerpt[:300]
        )
        mode = llm_client.mode

    return RagResult(
        answer=answer,
        sources=chunks,
        session_id=sid,
        llm_mode=mode,
        related_alerts=await _related_alerts(session, query),
        related_incidents=await _related_incidents(session, query),
    )
