"""Read/write the committed index snapshot (``fixtures/index.jsonl``).

The index is deliberately FLOAT-FREE: each row is a chunk's metadata + text +
``embed_key`` (the content-address of its vector in the cache). Vectors live only
in ``fixtures/embeddings/``. That keeps the diffable artifact deterministic and
byte-stable, and means the dense vectors are loaded on demand from the cache when
seeding Qdrant or running the eval.
"""

from __future__ import annotations

import json

from .config import INDEX_PATH
from .embed import read_cached

# The fields persisted to index.jsonl, in a fixed order (rows are written with
# sort_keys, so this list documents intent rather than controlling layout).
INDEX_FIELDS = (
    "point_id",
    "slug",
    "page_path",
    "heading",
    "anchor",
    "occurrence",
    "type",
    "chunk_index",
    "text",
    "content_hash",
    "embed_key",
)


def index_jsonl(records: list[dict]) -> str:
    """Canonical serialization: one JSON object per line, sorted keys, in the
    records' existing (slug, document) order. Trailing newline."""
    lines = [json.dumps({k: r[k] for k in INDEX_FIELDS}, sort_keys=True, ensure_ascii=False) for r in records]
    return "\n".join(lines) + "\n"


def read_index() -> list[dict]:
    rows: list[dict] = []
    for line in INDEX_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def load_vector(row: dict) -> list[float]:
    """Dense vector for an index row, from the committed cache."""
    return read_cached(row["embed_key"])
