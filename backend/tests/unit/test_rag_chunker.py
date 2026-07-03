"""RAG chunker unit tests."""

from app.rag.chunker import KNOWLEDGE_DIR, chunk_text, load_and_chunk_knowledge


def test_chunk_text_splits_long_content():
    text = "A" * 1200
    chunks = chunk_text(text, chunk_size=500, overlap=50)
    assert len(chunks) >= 2


def test_load_knowledge_has_document_ids():
    chunks = load_and_chunk_knowledge(KNOWLEDGE_DIR)
    assert len(chunks) >= 4
    doc_ids = {c.document_id for c in chunks}
    assert "sop-hot-work-001" in doc_ids
