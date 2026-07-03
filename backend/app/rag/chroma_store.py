"""ChromaDB vector store client."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

import chromadb

from app.config import settings

logger = logging.getLogger(__name__)

COLLECTION_NAME = "prism_knowledge"


def _parse_chroma_host_port(url: str) -> tuple[str, int]:
    parsed = urlparse(url)
    host = parsed.hostname or "chroma"
    port = parsed.port or 8000
    return host, port


def get_chroma_client() -> chromadb.HttpClient:
    host, port = _parse_chroma_host_port(settings.CHROMA_URL)
    return chromadb.HttpClient(host=host, port=port)


def get_or_create_collection(client: chromadb.HttpClient | None = None):
    client = client or get_chroma_client()
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def collection_count() -> int:
    try:
        collection = get_or_create_collection()
        return collection.count()
    except Exception:
        logger.exception("Failed to get Chroma collection count")
        return 0


def upsert_chunks(
    ids: list[str],
    documents: list[str],
    embeddings: list[list[float]],
    metadatas: list[dict],
) -> None:
    collection = get_or_create_collection()
    collection.upsert(
        ids=ids,
        documents=documents,
        embeddings=embeddings,
        metadatas=metadatas,
    )


def query_collection(
    query_embedding: list[float],
    top_k: int = 5,
) -> dict:
    collection = get_or_create_collection()
    return collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["documents", "metadatas", "distances"],
    )
