"""Qdrant store tests via local mode (no server, no Docker). Skipped entirely
when qdrant-client isn't installed (the lean [dev] CI), so collection is safe."""

from __future__ import annotations

import pytest

pytest.importorskip("qdrant_client")

from vrag import config as C  # noqa: E402
from vrag.embed import embed, normalize  # noqa: E402
from vrag.index_io import read_index  # noqa: E402
from vrag.retrieve import get_index  # noqa: E402
from vrag.stores import qdrant_store as Q  # noqa: E402

pytestmark = pytest.mark.skipif(not C.INDEX_PATH.exists(), reason="fixtures not built")


@pytest.fixture(scope="module")
def seeded():
    c = Q.client()  # in-process :memory:
    Q.ensure_collection(c, recreate=True)
    Q.seed(c)
    return c


def test_seed_count_matches_index(seeded):
    assert Q.count(seeded) == len(read_index())


def test_qdrant_dense_matches_bruteforce(seeded):
    """Qdrant COSINE ranking == in-process brute-force on every gold query (top-5)."""
    from evals.run import load_gold

    idx = get_index()
    for r in load_gold():
        qv = embed(r["query"], keyless=True)
        qd = [pid for pid, _ in Q.dense_search(seeded, qv, 10)]
        bf = [pid for pid, _ in idx.dense_ranked(normalize(qv), 10)]
        assert qd[:5] == bf[:5], f"{r['query_id']}: Qdrant vs brute-force diverged"
