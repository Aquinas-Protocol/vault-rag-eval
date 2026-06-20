"""Cloud retrieval backend: Qdrant (dense) + Neon Postgres (lexical), fused with
RRF. Same ``SearchHit`` shape and dense-default as the in-process backend; only
the stores differ. This is what the deployed FastAPI service calls.

The lexical arm here is Postgres. For exact identifiers the ``pg_trgm`` substring
arm is the workhorse (the tsvector parser splits on underscores); that is the
default lexical arm when hybrid is requested.
"""

from __future__ import annotations

from .config import FUSE_DEPTH, RRF_K
from .retrieve import SearchHit
from .rrf import rrf_fuse
from .stores import postgres_store as P
from .stores import qdrant_store as Q


class CloudBackend:
    def __init__(self, qclient, pconn=None) -> None:
        self.q = qclient
        self.p = pconn  # None -> dense-only (the shipped default needs no Postgres)

    def search(
        self,
        query: str,
        qvec: list[float],
        top_k: int = 8,
        *,
        hybrid: bool = False,
        lex_arms: tuple[str, ...] = ("trgm",),
        dense_weight: float = 3.0,
    ) -> list[SearchHit]:
        dense = Q.dense_search(self.q, qvec, FUSE_DEPTH)
        if hybrid and self.p is not None:
            lists: list[list[str]] = [[pid for pid, _ in dense]]
            weights: list[float] = [dense_weight]
            for arm in lex_arms:
                if arm == "trgm":
                    lists.append(P.trgm_search(self.p, query, FUSE_DEPTH))
                else:
                    lists.append(P.lexical_search(self.p, query, FUSE_DEPTH, config=arm))
                weights.append(1.0)
            scored = rrf_fuse(*lists, k=RRF_K, top_k=top_k, weights=weights)
        else:
            scored = [(pid, round(float(s), 6)) for pid, s in dense[:top_k]]

        pay = Q.fetch_payloads(self.q, [pid for pid, _ in scored])
        hits: list[SearchHit] = []
        for pid, score in scored:
            d = pay.get(pid)
            if not d:
                continue
            hits.append(
                SearchHit(
                    point_id=pid,
                    slug=d["slug"],
                    page_path=d["page_path"],
                    heading=d["heading"],
                    snippet=" ".join(d["text"].split())[:280],
                    score=round(float(score), 6),
                    chunk_index=d["chunk_index"],
                )
            )
        return hits
