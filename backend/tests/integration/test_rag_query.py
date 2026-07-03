"""Integration tests for RAG query endpoint."""

import pytest

from app.contract import PATH_RAG_QUERY


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rag_query_hot_work_sop(integration_client):
    response = await integration_client.post(
        PATH_RAG_QUERY,
        json={"query": "What are the hot work permit requirements before welding?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["answer"]) > 20
    assert data["llm_mode"] in ("mock", "live")
    assert len(data["sources"]) >= 1
    doc_ids = {s["document_id"] for s in data["sources"]}
    assert "sop-hot-work-001" in doc_ids


@pytest.mark.integration
@pytest.mark.asyncio
async def test_rag_query_session_id_persisted(integration_client):
    first = await integration_client.post(
        PATH_RAG_QUERY,
        json={"query": "confined space oxygen minimum"},
    )
    assert first.status_code == 200
    session_id = first.json()["session_id"]

    second = await integration_client.post(
        PATH_RAG_QUERY,
        json={"query": "what was that threshold again?", "session_id": session_id},
    )
    assert second.status_code == 200
    assert second.json()["session_id"] == session_id
