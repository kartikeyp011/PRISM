"""RAG query unit tests."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.rag.service import query_rag


@pytest.mark.asyncio
async def test_query_rag_mock_mode_with_sources():
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=mock_result)

    result = await query_rag(
        session,
        "What are the hot work permit requirements before welding?",
    )

    assert result.llm_mode == "mock"
    assert len(result.answer) > 20
    assert len(result.sources) >= 1
    assert any(s.document_id == "sop-hot-work-001" for s in result.sources)


@pytest.mark.asyncio
async def test_query_rag_confined_space_sources():
    session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    session.execute = AsyncMock(return_value=mock_result)

    result = await query_rag(session, "minimum oxygen level confined space entry")

    assert any(s.document_id == "sop-confined-space-001" for s in result.sources)
