"""Local embedding model using sentence-transformers."""

from __future__ import annotations

from functools import lru_cache

from app.config import settings

_model = None


@lru_cache
def _get_model_name() -> str:
    return settings.EMBEDDING_MODEL


def get_embedding_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer

        _model = SentenceTransformer(_get_model_name())
    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    model = get_embedding_model()
    vectors = model.encode(texts, normalize_embeddings=True)
    return [vector.tolist() for vector in vectors]


def embed_query(query: str) -> list[float]:
    return embed_texts([query])[0]
