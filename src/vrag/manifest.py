"""The index manifest: the single source of truth the eval harness checks a gold
set's ``config_version`` against. Deliberately free of any wall-clock timestamp or
machine-specific field so it is byte-reproducible (the git commit dates the build).
"""

from __future__ import annotations

import json

from . import config as C
from .corpus import corpus_hash


def build_manifest(chunk_count: int, pages: list[dict] | None = None) -> dict:
    return {
        "schema_version": 1,
        "corpus_hash": corpus_hash(pages),
        "chunker": {
            "id": C.CHUNKER_ID,
            "version": C.CHUNKER_VERSION,
            "target_chars": C.TARGET_CHARS,
            "min_chars": C.MIN_CHARS,
            "overlap": "1-paragraph",
        },
        "embedding": {"provider": "ollama", "model": C.EMBED_MODEL, "dim": C.EMBED_DIM},
        "lexical": {
            "engine": "postgres-tsvector",
            "config": ["simple", "english", "pg_trgm"],
            "rank": "ts_rank_cd",
            "note": "full-text ranking, not BM25 (no IDF/TF-saturation/length-norm)",
        },
        "fusion": {"method": "rrf", "k": C.RRF_K, "depth": C.FUSE_DEPTH},
        "config_version": C.CONFIG_VERSION,
        "chunk_count": chunk_count,
    }


def manifest_json(chunk_count: int, pages: list[dict] | None = None) -> str:
    """Canonical, deterministic serialization (sorted keys, trailing newline)."""
    return json.dumps(build_manifest(chunk_count, pages), indent=2, sort_keys=True) + "\n"
