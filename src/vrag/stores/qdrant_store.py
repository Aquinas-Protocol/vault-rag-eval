"""Qdrant dense-vector store adapter.

Dev/CI use the in-process local mode (``:memory:`` or a path) — no server, no
Docker. Prod points at the Fly-hosted Qdrant over ``.flycast`` with an API key.
The point id is the chunk's structure-keyed UUID, so ids are shared with Postgres
for RRF fusion. COSINE distance returns cosine similarity directly, matching the
in-process brute-force arm.
"""

from __future__ import annotations

import os

from qdrant_client import QdrantClient, models

from ..config import EMBED_DIM
from ..embed import read_cached
from ..index_io import read_index

COLLECTION = os.getenv("QDRANT_COLLECTION", "vrag_chunks")
DISTANCE = models.Distance.COSINE
_PAYLOAD_FIELDS = ("slug", "page_path", "heading", "chunk_index", "text")


def client(*, local_path: str | None = None) -> QdrantClient:
    """A QdrantClient from env (prod) or local mode (dev/CI).

    QDRANT_URL set -> remote (with QDRANT_API_KEY). Else a local path if given,
    else in-process ``:memory:``.
    """
    url = os.getenv("QDRANT_URL")
    if url:
        return QdrantClient(url=url, api_key=os.getenv("QDRANT_API_KEY"), timeout=30)
    if local_path:
        return QdrantClient(path=local_path)
    return QdrantClient(location=":memory:")


def ensure_collection(c: QdrantClient, name: str = COLLECTION, *, recreate: bool = False) -> None:
    if recreate and c.collection_exists(name):
        c.delete_collection(name)
    if not c.collection_exists(name):
        c.create_collection(name, vectors_config=models.VectorParams(size=EMBED_DIM, distance=DISTANCE))


def seed(c: QdrantClient, name: str = COLLECTION, rows: list[dict] | None = None) -> int:
    """Upsert every committed chunk (vector from the cache + slim payload)."""
    rows = rows if rows is not None else read_index()
    points = [
        models.PointStruct(
            id=r["point_id"],
            vector=read_cached(r["embed_key"]),
            payload={k: r[k] for k in _PAYLOAD_FIELDS},
        )
        for r in rows
    ]
    c.upsert(name, points=points, wait=True)
    return len(points)


def dense_search(c: QdrantClient, qvec: list[float], limit: int, name: str = COLLECTION) -> list[tuple[str, float]]:
    res = c.query_points(name, query=qvec, limit=limit, with_payload=False)
    return [(str(p.id), float(p.score)) for p in res.points]


def fetch_payloads(c: QdrantClient, ids: list[str], name: str = COLLECTION) -> dict[str, dict]:
    recs = c.retrieve(name, ids=ids, with_payload=True)
    return {str(r.id): (r.payload or {}) for r in recs}


def count(c: QdrantClient, name: str = COLLECTION) -> int:
    return c.count(name, exact=True).count
