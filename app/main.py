"""FastAPI demo service for the cloud deployment.

Serves a FIXED set of canned queries with COMMITTED precomputed embeddings — there
is no live-embedding box, so there is no API key to rotate and no per-keystroke
spend to DoS (the proof survives unwatched, per the design's "decouple proof from
uptime"). Dense is the default; ``mode=hybrid`` additionally exercises the Neon
Postgres lexical arm so the demo can visibly show where it helps (identifier
queries) and where dense already wins (paraphrase).

Reaches Qdrant over ``.flycast`` (env QDRANT_URL/QDRANT_API_KEY) and Neon over the
pooled URL (env NEON_DATABASE_URL). With no Postgres configured it runs dense-only.
"""

from __future__ import annotations

import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from vrag.cloud import CloudBackend
from vrag.config import FIXTURES_DIR
from vrag.embed import read_cached
from vrag.stores import postgres_store as P
from vrag.stores import qdrant_store as Q

DEMO = {d["id"]: d for d in json.loads((FIXTURES_DIR / "demo_queries.json").read_text(encoding="utf-8"))}
_state: dict = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    _state["qdrant"] = Q.client()
    _state["pg_enabled"] = bool(os.getenv("NEON_DATABASE_URL"))
    yield
    try:
        _state["qdrant"].close()
    except Exception:
        pass


app = FastAPI(title="vault-rag-eval demo", version="0.1.0", lifespan=lifespan)


@app.get("/healthz")
def healthz() -> dict:
    out = {"ok": True}
    try:
        out["qdrant_points"] = Q.count(_state["qdrant"])
    except Exception as e:  # noqa: BLE001
        out["ok"] = False
        out["qdrant_error"] = str(e)
    if _state.get("pg_enabled"):
        try:
            with P.connect() as conn:
                out["pg_chunks"] = P.count(conn)
        except Exception as e:  # noqa: BLE001
            out["ok"] = False
            out["pg_error"] = str(e)
    return out


@app.get("/demo")
def list_demo() -> dict:
    return {
        "note": "Canned queries with committed embeddings. ?mode=dense (default) or hybrid.",
        "queries": [{"id": d["id"], "query": d["query"], "kind": d["kind"], "relevant": d["relevant"]} for d in DEMO.values()],
    }


@app.get("/demo/{query_id}")
def run_demo(query_id: str, mode: str = "dense", top_k: int = 5) -> dict:
    d = DEMO.get(query_id)
    if not d:
        raise HTTPException(404, f"unknown demo query {query_id!r}")
    qvec = read_cached(d["embed_key"])
    hybrid = mode == "hybrid"
    pconn = P.connect() if (hybrid and _state.get("pg_enabled")) else None
    try:
        backend = CloudBackend(_state["qdrant"], pconn)
        hits = backend.search(d["query"], qvec, top_k=top_k, hybrid=hybrid)
    finally:
        if pconn is not None:
            pconn.close()
    return {
        "id": d["id"],
        "query": d["query"],
        "kind": d["kind"],
        "relevant": d["relevant"],
        "mode": "hybrid" if (hybrid and _state.get("pg_enabled")) else "dense",
        "hits": [{"slug": h.slug, "heading": h.heading, "score": h.score, "snippet": h.snippet} for h in hits],
    }
