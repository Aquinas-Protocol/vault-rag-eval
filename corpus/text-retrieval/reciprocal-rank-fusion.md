---
title: "Reciprocal Rank Fusion"
type: concept
sources: []
related:
  - "[[tf-idf-ranking]]"
  - "[[vector-embeddings-ann]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Reciprocal Rank Fusion

## Overview
Reciprocal rank fusion is a simple way to merge several ranked result lists into one combined ordering. Rather than trying to reconcile the different score scales each system produces, it ignores the raw scores entirely and looks only at the position an item holds in each list. Items that rank near the top across multiple lists rise to the top of the fused result.

## Key Points
- Combines outputs from multiple retrievers without needing their scores to be comparable.
- Each item earns points based on its rank position, with higher positions worth more.
- A small constant added to the rank prevents the very top slot from dominating unfairly.
- Points from every list are summed, and items are reordered by their total.
- Robust by design: a single noisy ranker cannot easily push a bad item to the top.
- Widely used to blend keyword search with semantic search in hybrid retrieval.

## Details
The method assigns each item a contribution of one divided by a constant plus its rank in a given list. Because the score depends on position rather than magnitude, a keyword ranker and a vector ranker can be fused even though one emits cosine similarities and the other emits weighted term sums. The contributions across all input lists are added, and the merged list is sorted by that sum.

The added constant, often written as RRF_RANK_DAMPING in implementations, controls how steeply early ranks are favored. A larger value flattens the curve so that ranks two and three count nearly as much as rank one, while a smaller value sharply rewards the top position. Tuning it trades off between trusting any single list's leader and rewarding broad agreement.

Fusion is especially valuable in hybrid search, where a lexical method like [[tf-idf-ranking]] and a dense method like [[vector-embeddings-ann]] each surface documents the other misses. Blending their rankings tends to outperform either alone because the strengths are complementary: exact term matching plus semantic similarity.
