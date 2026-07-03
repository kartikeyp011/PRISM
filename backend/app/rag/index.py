"""CLI to chunk, embed, and upsert knowledge docs into ChromaDB."""

from __future__ import annotations

import logging
import sys

from app.rag.chunker import KNOWLEDGE_DIR, load_and_chunk_knowledge
from app.rag.chroma_store import collection_count, upsert_chunks
from app.rag.embedder import embed_texts

logger = logging.getLogger(__name__)


def index_knowledge(force: bool = False) -> int:
    if not force and collection_count() > 0:
        logger.info("Chroma collection already indexed (%d chunks)", collection_count())
        return collection_count()

    chunks = load_and_chunk_knowledge(KNOWLEDGE_DIR)
    if not chunks:
        logger.warning("No knowledge documents found in %s", KNOWLEDGE_DIR)
        return 0

    texts = [c.text for c in chunks]
    embeddings = embed_texts(texts)
    ids = [f"{c.document_id}-{c.chunk_index}" for c in chunks]
    metadatas = [
        {
            "document_id": c.document_id,
            "title": c.title,
            "source_file": c.source_file,
            "chunk_index": c.chunk_index,
        }
        for c in chunks
    ]

    upsert_chunks(ids=ids, documents=texts, embeddings=embeddings, metadatas=metadatas)
    count = len(chunks)
    logger.info("Indexed %d chunks from %s", count, KNOWLEDGE_DIR)
    return count


def ensure_indexed() -> int:
    try:
        return index_knowledge(force=False)
    except Exception:
        logger.exception("Knowledge indexing failed")
        return 0


def main() -> int:
    logging.basicConfig(level=logging.INFO)
    force = "--force" in sys.argv
    try:
        count = index_knowledge(force=force)
        print(f"Indexed {count} chunks into ChromaDB")
        return 0
    except Exception as exc:
        print(f"Indexing failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
