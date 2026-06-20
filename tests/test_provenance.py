"""Provenance gate: every committed data artifact must be regenerable from the
synthetic corpus + the committed embedding cache, with no model and no key.

This is the allowlist inversion the design calls for: anything in the index or the
manifest that is NOT derivable from ``corpus/`` fails the build. Plus a denylist
tripwire over the corpus and committed JSON.
"""

from __future__ import annotations

import json

import pytest

import vrag.embed as _embed
from vrag import config as C
from vrag.corpus import build_chunk_records, load_pages
from vrag.index_io import index_jsonl
from vrag.manifest import manifest_json

pytestmark = pytest.mark.skipif(not C.INDEX_PATH.exists(), reason="fixtures not built yet")


def _committed(path):
    return path.read_text(encoding="utf-8")


def test_index_is_regenerable_byte_identical():
    pages = load_pages()
    records = build_chunk_records(pages)
    assert index_jsonl(records) == _committed(C.INDEX_PATH), (
        "fixtures/index.jsonl is not byte-identical to a fresh rebuild from corpus/ "
        "— run `make fixtures` and commit."
    )


def test_manifest_is_regenerable_byte_identical():
    pages = load_pages()
    records = build_chunk_records(pages)
    assert manifest_json(len(records), pages) == _committed(C.MANIFEST_PATH)


def test_manifest_chunk_count_matches_index():
    manifest = json.loads(_committed(C.MANIFEST_PATH))
    n_index = sum(1 for line in _committed(C.INDEX_PATH).splitlines() if line.strip())
    assert manifest["chunk_count"] == n_index


def test_every_indexed_chunk_has_a_cached_vector():
    for line in _committed(C.INDEX_PATH).splitlines():
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)
        vec = _embed.read_cached(row["embed_key"])
        assert len(vec) == _embed.EMBED_DIM, f"{row['point_id']}: wrong dim {len(vec)}"


def test_every_gold_query_has_a_cached_vector():
    if not C.GOLD_PATH.exists():
        pytest.skip("no gold set yet")
    for line in C.GOLD_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        q = json.loads(line).get("query", "").strip()
        if q:
            vec = _embed.read_cached(_embed.cache_key(q))
            assert len(vec) == _embed.EMBED_DIM


def test_denylist_clean():
    from scripts import denylist_scan  # noqa: PLC0415

    hashes = denylist_scan._load_hashes()
    assert hashes, "scripts/denylist.sha256 missing or empty"
    violations = denylist_scan.scan_tree(hashes)
    assert not violations, "denylist violations:\n" + "\n".join(violations)
