"""Reciprocal Rank Fusion. Pure and dependency-free."""

from __future__ import annotations

from .config import RRF_K


def rrf_fuse(
    *ranked_lists: list[str],
    k: int = RRF_K,
    top_k: int = 10,
    weights: list[float] | None = None,
) -> list[tuple[str, float]]:
    """Fuse N ranked id lists. score(id) = sum_i w_i / (k + rank_i), rank 1-based;
    w_i defaults to 1. Consumes only rank position, so heterogeneous arm scores
    (cosine vs ts_rank) need no normalization. Per-list weights let a stronger arm
    outvote a noisier one without touching score scales. Returns (id, score)
    best-first.
    """
    if weights is None:
        weights = [1.0] * len(ranked_lists)
    scores: dict[str, float] = {}
    for weight, ranked in zip(weights, ranked_lists):
        for rank, doc_id in enumerate(ranked, start=1):
            scores[doc_id] = scores.get(doc_id, 0.0) + weight / (k + rank)
    ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return ordered[:top_k]
