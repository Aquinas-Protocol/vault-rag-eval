"""Keyless retrieval for the eval: drive the REAL production ``search()`` with a
cached query embedding and return distinct slugs in rank order. Importing the
shipped path (not a re-implementation) is the whole point — the gate measures what
production does."""

from __future__ import annotations

from vrag.retrieve import search


def ranked_slugs(
    query: str,
    qvec: list[float],
    *,
    hybrid: bool = False,
    lex_arms: tuple[str, ...] = ("exact",),
    dense_weight: float = 3.0,
    depth: int = 50,
) -> list[str]:
    hits = search(
        query,
        top_k=depth,
        query_vec=qvec,
        hybrid=hybrid,
        lex_arms=lex_arms,
        dense_weight=dense_weight,
    )
    out: list[str] = []
    seen: set[str] = set()
    for h in hits:
        if h.slug not in seen:
            seen.add(h.slug)
            out.append(h.slug)
    return out
