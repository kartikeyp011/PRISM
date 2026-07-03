"""ComplianceAgent — RAG over SOPs, regulations, and incident reports."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.rag.service import RagResult, query_rag


class ComplianceAgent:
    async def ask(
        self,
        session: AsyncSession,
        query: str,
        session_id: str | None = None,
        top_k: int = 5,
    ) -> RagResult:
        return await query_rag(session, query, session_id=session_id, top_k=top_k)


compliance_agent = ComplianceAgent()
