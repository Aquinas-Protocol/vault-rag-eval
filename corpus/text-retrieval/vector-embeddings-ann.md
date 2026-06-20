---
title: "Vector Embeddings and ANN"
type: concept
sources: []
related:
  - "[[stemming-and-tokenization]]"
  - "[[reciprocal-rank-fusion]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Vector Embeddings and ANN

## Overview
Vector embeddings turn text into lists of numbers so that meaning, not just exact wording, drives retrieval. A model maps each passage to a point in a high-dimensional space where similar ideas land close together, even when they share no words. Approximate nearest neighbor search is the technique that finds the closest of those points quickly, trading a little accuracy for a large speedup.

## Key Points
- An embedding model converts text into a fixed-length numeric vector capturing semantic meaning.
- Closeness in vector space reflects similarity of meaning, so paraphrases match even without shared terms.
- Similarity is typically measured by cosine angle or dot product between vectors.
- Exact nearest-neighbor search over millions of vectors is too slow, motivating approximate methods.
- Graph and partition-based indexes prune the search space to return likely neighbors fast.
- Dense semantic search complements lexical search, which is why the two are often fused.

## Details
An embedding model is trained so that passages with related meaning produce vectors pointing in similar directions. At query time the question is embedded with the same model, and retrieval becomes a geometry problem: find the stored vectors nearest to the query vector. This captures matches that keyword search misses, such as a document that answers a question using entirely different vocabulary.

Searching every vector exhaustively does not scale, so approximate nearest neighbor indexes are used. Graph-based structures connect each vector to a handful of neighbors and walk the graph greedily toward the query; partitioning structures group vectors into cells and probe only the most promising ones. A tunable parameter often named ANN_PROBE_BUDGET caps how many candidates are examined, directly trading recall for latency. Raising it finds more true neighbors at the cost of speed.

Because the input text is first cleaned by the pipeline in [[stemming-and-tokenization]], embeddings see consistent input. Dense results are frequently combined with lexical rankings through [[reciprocal-rank-fusion]], giving a hybrid system that matches both exact terms and underlying meaning.
