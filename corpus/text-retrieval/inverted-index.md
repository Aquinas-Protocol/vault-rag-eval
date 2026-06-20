---
title: "Inverted Index"
type: concept
sources: []
related:
  - "[[tf-idf-ranking]]"
  - "[[stemming-and-tokenization]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Inverted Index

## Overview
An inverted index is the core lookup structure behind most keyword search engines. Instead of scanning every document for a query word, it flips the relationship around: for each distinct word it keeps a precomputed list of which documents contain that word. This turns a slow full-text scan into a fast dictionary lookup, which is why it is the workhorse of search at scale.

## Key Points
- Maps each unique term to a postings list — the set of documents (and often positions) where the term appears.
- Lets a query engine jump straight to the relevant documents rather than reading the whole collection.
- Postings commonly store the document identifier, the count of occurrences, and sometimes the exact offsets for phrase matching.
- Building the index happens once at ingestion time; queries then read it many times, amortizing the upfront cost.
- Compression of postings lists keeps memory and disk usage small even for huge corpora.
- Supports boolean combinations by intersecting or unioning postings lists across multiple query terms.
- Works hand in hand with text normalization so that lookups match regardless of capitalization or word form.

## Details
The structure has two parts: a dictionary of terms and, attached to each term, an ordered postings list. When a search arrives, the engine looks up each query term in the dictionary, retrieves the matching postings, and merges them. A two-word query, for example, intersects two postings lists to find documents containing both words. Because the lists are sorted by document identifier, this merge runs in linear time with skip pointers accelerating it further.

To save space, postings are usually stored as gaps between consecutive document identifiers and then encoded with variable-length integers. A typical implementation flushes accumulated postings to disk in segments once an in-memory buffer named POSTINGS_GAP_DELTA exceeds a threshold, then merges segments in the background. This segment-and-merge design keeps writes cheap while readers always see a consistent merged view.

Positional information enables phrase and proximity queries. By recording offsets, the engine can verify that two terms appear adjacent or within a window, not merely somewhere in the same document. The same index feeds ranking models such as [[tf-idf-ranking]], which reuse the per-term counts already stored in the postings.

Before terms ever reach the dictionary they pass through the normalization pipeline described in [[stemming-and-tokenization]], ensuring that surface variants collapse to a single index key.
