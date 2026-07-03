"""Demo CV sample images for offline analysis."""

from __future__ import annotations

from pathlib import Path

SAMPLES_DIR = Path(__file__).resolve().parents[2] / "data" / "cv_samples"

SAMPLE_CATALOG: dict[str, dict[str, str]] = {
    "compliant_worker": {
        "title": "Compliant Worker",
        "description": "Worker with hard hat and safety vest — no hazards expected.",
    },
    "no_ppe_worker": {
        "title": "Missing PPE",
        "description": "Worker without hard hat or safety vest — PPE violation.",
    },
    "hot_work_scene": {
        "title": "Hot Work Scene",
        "description": "Welding activity detected in monitored zone.",
    },
}


def ensure_sample_images() -> None:
    """Create minimal PNG placeholders if missing (first run / fresh clone)."""
    try:
        from PIL import Image, ImageDraw
    except ImportError:
        return

    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    specs = {
        "compliant_worker": ("#334155", "#22c55e", "#eab308"),
        "no_ppe_worker": ("#334155", "#ef4444", "#64748b"),
        "hot_work_scene": ("#1e293b", "#f97316", "#ef4444"),
    }
    for sample_id, colors in specs.items():
        path = SAMPLES_DIR / f"{sample_id}.png"
        if path.exists():
            continue
        img = Image.new("RGB", (640, 480), colors[0])
        draw = ImageDraw.Draw(img)
        draw.rectangle((180, 120, 460, 420), fill=colors[1])
        draw.ellipse((260, 60, 380, 180), fill=colors[2])
        img.save(path)


def list_samples() -> list[dict[str, str]]:
    ensure_sample_images()
    samples = []
    for sample_id, meta in SAMPLE_CATALOG.items():
        path = SAMPLES_DIR / f"{sample_id}.png"
        samples.append(
            {
                "sample_id": sample_id,
                "title": meta["title"],
                "description": meta["description"],
                "available": path.exists(),
            }
        )
    return samples


def sample_path(sample_id: str) -> Path | None:
    if sample_id not in SAMPLE_CATALOG:
        return None
    ensure_sample_images()
    path = SAMPLES_DIR / f"{sample_id}.png"
    return path if path.exists() else None
