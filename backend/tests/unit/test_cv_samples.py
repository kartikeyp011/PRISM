"""CV samples catalog unit tests."""

from app.cv.samples import SAMPLE_CATALOG, list_samples


def test_list_samples_has_demo_entries():
    samples = list_samples()
    assert len(samples) == len(SAMPLE_CATALOG)
    ids = {s["sample_id"] for s in samples}
    assert "no_ppe_worker" in ids
    assert "compliant_worker" in ids
    assert all(s["available"] for s in samples)
