"""HTTP client for remote LLM (Ollama via ngrok) with mock fallback."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

MOCK_RAG_ANSWER = (
    "Based on seeded SOP documents (mock mode): Hot work permits require "
    "gas monitoring, fire watch assignment, and area isolation before welding "
    "begins. Confined space entry requires continuous atmospheric monitoring "
    "with minimum 19.5% oxygen."
)

MOCK_CHAT_RESPONSE = (
    "This is a mock LLM response. Set LLM_BASE_URL in .env to use the live "
    "Kaggle Ollama endpoint."
)


@dataclass
class ChatMessage:
    role: str
    content: str


@dataclass
class ChatResult:
    content: str
    mode: str  # live | mock


@dataclass
class EmbeddingResult:
    embeddings: list[list[float]]
    mode: str  # live | mock


class LLMClient:
    """OpenAI-compatible client for remote Ollama; mock mode when URL unset."""

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout: float = 60.0,
    ) -> None:
        self.base_url = (base_url if base_url is not None else settings.LLM_BASE_URL).rstrip("/")
        self.model = model or settings.LLM_MODEL
        self.timeout = timeout

    @property
    def is_mock(self) -> bool:
        return not self.base_url

    @property
    def mode(self) -> str:
        return "mock" if self.is_mock else "live"

    async def chat(self, messages: list[ChatMessage], **kwargs: Any) -> ChatResult:
        if self.is_mock:
            # Return RAG-style answer if context keywords present
            combined = " ".join(m.content.lower() for m in messages)
            content = MOCK_RAG_ANSWER if any(
                kw in combined for kw in ("sop", "permit", "osha", "confined", "hot work")
            ) else MOCK_CHAT_RESPONSE
            return ChatResult(content=content, mode="mock")

        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            **kwargs,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return ChatResult(content=content, mode="live")

    async def embeddings(self, texts: list[str]) -> EmbeddingResult:
        """Request embeddings from remote LLM or return deterministic mock vectors."""
        if self.is_mock:
            return EmbeddingResult(
                embeddings=[[float(i % 7) / 7.0 for i in range(384)] for _ in texts],
                mode="mock",
            )

        url = f"{self.base_url}/v1/embeddings"
        payload = {"model": self.model, "input": texts}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            vectors = [item["embedding"] for item in data["data"]]
            return EmbeddingResult(embeddings=vectors, mode="live")

    async def health_check(self) -> dict[str, Any]:
        if self.is_mock:
            return {"status": "mock", "reachable": True}

        url = f"{self.base_url}/api/tags"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return {"status": "live", "reachable": True, "tags": response.json()}


llm_client = LLMClient()
