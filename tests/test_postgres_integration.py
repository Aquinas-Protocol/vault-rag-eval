"""Neon Postgres integration — runs only when NEON_DATABASE_URL points at a seeded
database (so keyless CI skips it). Verifies the lexical arm resolves identifiers and
that the cloud hybrid path rescues an identifier query dense misses."""

from __future__ import annotations

import json
import os

import pytest

pytest.importorskip("psycopg")
pytest.importorskip("qdrant_client")

if not os.getenv("NEON_DATABASE_URL"):
    pytest.skip("NEON_DATABASE_URL not set", allow_module_level=True)

from vrag.cloud import CloudBackend  # noqa: E402
from vrag.config import FIXTURES_DIR  # noqa: E402
from vrag.embed import read_cached  # noqa: E402
from vrag.index_io import read_index  # noqa: E402
from vrag.stores import postgres_store as P  # noqa: E402
from vrag.stores import qdrant_store as Q  # noqa: E402

_SLUG = {r["point_id"]: r["slug"] for r in read_index()}


@pytest.fixture(scope="module")
def conn():
    c = P.connect()
    if P.count(c) == 0:
        pytest.skip("Neon reachable but not seeded (run scripts/seed_stores.py --postgres)")
    yield c
    c.close()


def test_trgm_resolves_identifier(conn):
    pids = P.trgm_search(conn, "what does the FENCING_EPOCH_ID guard value do", 5)
    assert pids, "trgm arm returned nothing for an identifier query"
    assert "leader-election" in {_SLUG[p] for p in pids}


def test_hybrid_rescues_identifier_query_dense_misses(conn):
    qc = Q.client()
    Q.ensure_collection(qc, recreate=True)
    Q.seed(qc)
    demo = {d["id"]: d for d in json.loads((FIXTURES_DIR / "demo_queries.json").read_text(encoding="utf-8"))}
    d = demo["d01"]
    qv = read_cached(d["embed_key"])
    dense = [h.slug for h in CloudBackend(qc, None).search(d["query"], qv, top_k=3)]
    hybrid = [
        h.slug
        for h in CloudBackend(qc, conn).search(
            d["query"], qv, top_k=3, hybrid=True, lex_arms=("trgm",), dense_weight=1.0
        )
    ]
    assert "leader-election" not in dense, "dense unexpectedly already found the identifier page"
    assert "leader-election" in hybrid, "hybrid failed to rescue the identifier query"
