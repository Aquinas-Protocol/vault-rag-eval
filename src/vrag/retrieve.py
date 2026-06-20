"""In-process retrieval backend (the ``local`` side of the backend seam).

Loads the committed index + vectors and serves dense, lexical, and hybrid
retrieval with no external service — exact cosine over the committed vectors plus
sqlite FTS5 (genuine ``bm25()``) for the lexical arm. This is what dev and the
fast keyless eval run against. The deployed ``cloud`` backend (Qdrant for dense,
Neon Postgres ``tsvector`` for lexical) implements the same ``search()`` shape and
RRF fusion; only the stores change.

Default is dense. Hybrid (dense + FTS5 arms fused with RRF) is opt-in, with the
dense arm up-weighted — the honest sweep found dense >= hybrid on this corpus, the
same finding as the private original.
"""

from __future__ import annotations

import math
import re
import sqlite3
from dataclasses import dataclass
from functools import lru_cache

from .config import FUSE_DEPTH, RRF_K
from .embed import embed, normalize, read_cached
from .index_io import read_index
from .rrf import rrf_fuse

_FTS_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")

DENSE_WEIGHT_DEFAULT = 3.0
LEX_ARMS_DEFAULT = ("exact",)


@dataclass(frozen=True)
class SearchHit:
    point_id: str
    slug: str
    page_path: str
    heading: str
    snippet: str
    score: float
    chunk_index: int


class LocalIndex:
    """The committed index loaded into memory + an in-memory sqlite FTS5 mirror."""

    def __init__(self) -> None:
        rows = read_index()
        self.meta: dict[str, tuple] = {}
        self.vectors: list[tuple[str, list[float]]] = []
        con = sqlite3.connect(":memory:")
        con.execute("CREATE TABLE chunks (rowid INTEGER PRIMARY KEY, point_id TEXT, text TEXT)")
        # External-content FTS5: no text duplication; two tokenizations — exact-token
        # (underscores kept attached, so MAX_POOL_LEASE_COUNT is one token) and
        # trigram (substring, so 'pool_lea' finds it).
        con.execute(
            "CREATE VIRTUAL TABLE chunks_fts USING fts5("
            "text, content='chunks', content_rowid='rowid', tokenize=\"unicode61 tokenchars '_'\")"
        )
        con.execute(
            "CREATE VIRTUAL TABLE chunks_fts_tri USING fts5("
            "text, content='chunks', content_rowid='rowid', tokenize='trigram')"
        )
        for i, r in enumerate(rows, start=1):
            pid = r["point_id"]
            con.execute("INSERT INTO chunks(rowid, point_id, text) VALUES (?,?,?)", (i, pid, r["text"]))
            self.meta[pid] = (r["slug"], r["page_path"], r["heading"], r["chunk_index"], r["text"])
            self.vectors.append((pid, normalize(read_cached(r["embed_key"]))))
        con.execute("INSERT INTO chunks_fts(chunks_fts) VALUES('rebuild')")
        con.execute("INSERT INTO chunks_fts_tri(chunks_fts_tri) VALUES('rebuild')")
        self.con = con

    def dense_ranked(self, qv: list[float], depth: int) -> list[tuple[str, float]]:
        scored = [(pid, math.fsum(q * e for q, e in zip(qv, vec))) for pid, vec in self.vectors]
        scored.sort(key=lambda t: t[1], reverse=True)
        return scored[:depth]

    def lexical_ranked(self, query: str, arm: str, depth: int) -> list[str]:
        table, min_len = ("chunks_fts", 2) if arm == "exact" else ("chunks_fts_tri", 3)
        fq = _fts_query(query, min_len)
        if not fq:
            return []
        rows = self.con.execute(
            f"SELECT c.point_id FROM {table} JOIN chunks c ON c.rowid = {table}.rowid "
            f"WHERE {table} MATCH ? ORDER BY bm25({table}) LIMIT ?",
            (fq, depth),
        ).fetchall()
        return [r[0] for r in rows]


def _fts_query(text: str, min_len: int) -> str:
    """Free text -> a safe FTS5 MATCH string: word tokens (underscores kept), drop
    tokens under min_len, de-dup, phrase-quote (escapes FTS operators), OR-join."""
    seen: set[str] = set()
    terms: list[str] = []
    for t in _FTS_TOKEN_RE.findall(text):
        if len(t) < min_len:
            continue
        low = t.lower()
        if low in seen:
            continue
        seen.add(low)
        terms.append(t)
    return " OR ".join(f'"{t}"' for t in terms[:32])


@lru_cache(maxsize=1)
def get_index() -> LocalIndex:
    return LocalIndex()


def search(
    query: str,
    top_k: int = 8,
    *,
    query_vec: list[float] | None = None,
    hybrid: bool = False,
    lex_arms: tuple[str, ...] = LEX_ARMS_DEFAULT,
    dense_weight: float = DENSE_WEIGHT_DEFAULT,
) -> list[SearchHit]:
    """THE shared query path. Dense cosine by default; hybrid fuses the dense arm
    with the requested FTS5 lexical arms via RRF (dense up-weighted).

    ``query_vec`` injects a precomputed (cached) embedding so the eval drives this
    exact path keylessly; production omits it and embeds. Lexical arms always use
    the query text.
    """
    top_k = max(1, min(int(top_k), 50))
    idx = get_index()
    qv = normalize(query_vec if query_vec is not None else embed(query))
    dense = idx.dense_ranked(qv, FUSE_DEPTH)

    if hybrid:
        lists: list[list[str]] = [[pid for pid, _ in dense]]
        weights: list[float] = [dense_weight]
        for arm in lex_arms:
            lists.append(idx.lexical_ranked(query, arm, FUSE_DEPTH))
            weights.append(1.0)
        scored = rrf_fuse(*lists, k=RRF_K, top_k=top_k, weights=weights)
    else:
        scored = [(pid, round(float(s), 6)) for pid, s in dense[:top_k]]

    hits: list[SearchHit] = []
    for pid, score in scored:
        data = idx.meta.get(pid)
        if data is None:
            continue
        slug, page_path, heading, cidx, text = data
        hits.append(
            SearchHit(
                point_id=pid,
                slug=slug,
                page_path=page_path,
                heading=heading,
                snippet=" ".join(text.split())[:280],
                score=round(float(score), 6),
                chunk_index=cidx,
            )
        )
    return hits
