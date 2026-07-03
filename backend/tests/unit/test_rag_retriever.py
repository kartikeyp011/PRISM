"""RAG retriever unit tests."""

from app.rag.retriever import keyword_retrieve


def test_keyword_retrieve_hot_work_query():
    results = keyword_retrieve("hot work permit requirements welding", top_k=3)
    assert len(results) >= 1
    doc_ids = {r.document_id for r in results}
    assert "sop-hot-work-001" in doc_ids


def test_keyword_retrieve_confined_space_o2():
    results = keyword_retrieve("minimum oxygen level confined space entry", top_k=3)
    assert len(results) >= 1
    doc_ids = {r.document_id for r in results}
    assert "sop-confined-space-001" in doc_ids


def test_keyword_retrieve_incident_report():
    results = keyword_retrieve("compound gas spike incident", top_k=3)
    assert len(results) >= 1
    doc_ids = {r.document_id for r in results}
    assert "incident-compound-gas-001" in doc_ids


def test_keyword_retrieve_no_match():
    results = keyword_retrieve("xyznonexistentquery123", top_k=3)
    assert results == []
