"""Hand-rolled ranking metrics. Zero deps so the keyless gate stays hermetic.
Page-level (slug) relevance: "did a chunk of a relevant page surface in the top
k?" — the real success criterion for RAG over this corpus, and robust to
re-chunking. ``ranked`` is a list of DISTINCT slugs, best first.
"""

from __future__ import annotations


def recall_at_k(ranked: list[str], relevant: list[str], k: int) -> float:
    rel = set(relevant)
    if not rel:
        return 0.0
    return len(set(ranked[:k]) & rel) / len(rel)


def precision_at_k(ranked: list[str], relevant: list[str], k: int) -> float:
    if k <= 0:
        return 0.0
    return len(set(ranked[:k]) & set(relevant)) / k


def hit_rate_at_k(ranked: list[str], relevant: list[str], k: int) -> float:
    return 1.0 if set(ranked[:k]) & set(relevant) else 0.0


def mrr_at_k(ranked: list[str], relevant: list[str], k: int) -> float:
    rel = set(relevant)
    for i, slug in enumerate(ranked[:k], start=1):
        if slug in rel:
            return 1.0 / i
    return 0.0
