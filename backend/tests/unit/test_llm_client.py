"""LLM client unit tests."""

import os

import pytest

from app.services.llm_client import ChatMessage, LLMClient


@pytest.mark.asyncio
async def test_mock_mode_when_url_empty():
    client = LLMClient(base_url="", model="llama3.2")
    assert client.is_mock
    assert client.mode == "mock"

    result = await client.chat([ChatMessage(role="user", content="Hello")])
    assert result.mode == "mock"
    assert len(result.content) > 0


@pytest.mark.asyncio
async def test_mock_rag_answer_for_compliance_query():
    client = LLMClient(base_url="")
    result = await client.chat([
        ChatMessage(role="user", content="What are the hot work permit requirements?"),
    ])
    assert "hot work" in result.content.lower() or "permit" in result.content.lower()


@pytest.mark.asyncio
async def test_mock_embeddings():
    client = LLMClient(base_url="")
    result = await client.embeddings(["test text"])
    assert result.mode == "mock"
    assert len(result.embeddings) == 1
    assert len(result.embeddings[0]) == 384


@pytest.mark.asyncio
async def test_mock_health_check():
    client = LLMClient(base_url="")
    health = await client.health_check()
    assert health["status"] == "mock"
    assert health["reachable"] is True


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.environ.get("LLM_BASE_URL"),
    reason="LLM_BASE_URL not set — live integration skipped",
)
async def test_live_llm_health_check():
    client = LLMClient(base_url=os.environ["LLM_BASE_URL"])
    health = await client.health_check()
    assert health["reachable"] is True
