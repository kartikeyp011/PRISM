"""Text chunking for knowledge documents."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

KNOWLEDGE_DIR = Path(__file__).resolve().parents[2] / "data" / "knowledge"


@dataclass
class DocumentChunk:
    document_id: str
    title: str
    source_file: str
    text: str
    chunk_index: int


def _extract_document_id(content: str, filename: str) -> str:
    match = re.search(r"Document ID:\s*(\S+)", content)
    if match:
        return match.group(1)
    return Path(filename).stem


def _extract_title(content: str, filename: str) -> str:
    first_line = content.strip().split("\n", 1)[0].strip()
    return first_line if first_line else Path(filename).stem.replace("_", " ").title()


def chunk_text(text: str, chunk_size: int = 500, overlap: int = 80) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}".strip() if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) <= chunk_size:
                current = para
            else:
                start = 0
                while start < len(para):
                    end = start + chunk_size
                    chunks.append(para[start:end])
                    start = end - overlap
                current = ""

    if current:
        chunks.append(current)

    return chunks


def load_and_chunk_knowledge(knowledge_dir: Path) -> list[DocumentChunk]:
    results: list[DocumentChunk] = []
    for path in sorted(knowledge_dir.glob("*.txt")):
        content = path.read_text(encoding="utf-8")
        doc_id = _extract_document_id(content, path.name)
        title = _extract_title(content, path.name)
        for index, chunk in enumerate(chunk_text(content)):
            results.append(
                DocumentChunk(
                    document_id=doc_id,
                    title=title,
                    source_file=path.name,
                    text=chunk,
                    chunk_index=index,
                )
            )
    return results
