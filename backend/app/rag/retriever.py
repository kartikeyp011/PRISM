"""Document retrieval — ChromaDB with keyword fallback."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from app.rag.chunker import KNOWLEDGE_DIR, load_and_chunk_knowledge
from app.rag.chroma_store import query_collection
from app.rag.embedder import embed_query

logger = logging.getLogger(__name__)


@dataclass
class RetrievedChunk:
    document_id: str
    title: str
    excerpt: str
    score: float


def _keyword_score(query: str, text: str) -> float:
    tokens = {t for t in re.findall(r"[a-z0-9]+", query.lower()) if len(t) > 2}
    if not tokens:
        return 0.0
    text_lower = text.lower()
    hits = sum(1 for t in tokens if t in text_lower)
    return hits / len(tokens)


def keyword_retrieve(query: str, top_k: int = 5) -> list[RetrievedChunk]:
    chunks = load_and_chunk_knowledge(KNOWLEDGE_DIR)
    scored = [
        (
            _keyword_score(query, chunk.text),
            chunk,
        )
        for chunk in chunks
    ]
    scored.sort(key=lambda x: x[0], reverse=True)
    results: list[RetrievedChunk] = []
    for score, chunk in scored[:top_k]:
        if score <= 0:
            continue
        results.append(
            RetrievedChunk(
                document_id=chunk.document_id,
                title=chunk.title,
                excerpt=chunk.text[:400],
                score=round(score, 3),
            )
        )
    return results


def chroma_retrieve(query: str, top_k: int = 5) -> list[RetrievedChunk]:
    embedding = embed_query(query)
    result = query_collection(embedding, top_k=top_k)

    documents = result.get("documents", [[]])[0]
    metadatas = result.get("metadatas", [[]])[0]
    distances = result.get("distances", [[]])[0]

    chunks: list[RetrievedChunk] = []
    for doc, meta, dist in zip(documents, metadatas, distances, strict=False):
        if not doc or not meta:
            continue
        score = max(0.0, 1.0 - float(dist))
        chunks.append(
            RetrievedChunk(
                document_id=str(meta.get("document_id", "unknown")),
                title=str(meta.get("title", "Unknown")),
                excerpt=str(doc)[:400],
                score=round(score, 3),
            )
        )
    return chunks


def retrieve(query: str, top_k: int = 5) -> list[RetrievedChunk]:
    try:
        from app.rag.chroma_store import collection_count

        if collection_count() > 0:
            return chroma_retrieve(query, top_k=top_k)
    except Exception:
        logger.exception("Chroma retrieval failed — using keyword fallback")

    return keyword_retrieve(query, top_k=top_k)
