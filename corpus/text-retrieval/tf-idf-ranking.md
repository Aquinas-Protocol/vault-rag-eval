---
title: "TF-IDF Ranking"
type: concept
sources: []
related:
  - "[[inverted-index]]"
  - "[[reciprocal-rank-fusion]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# TF-IDF Ranking

## Overview
TF-IDF is a classic scoring scheme that decides how relevant a document is to a search by balancing two intuitions: a word matters more when it shows up often in a document, but matters less when it is common across the whole collection. Multiplying these two signals gives each term a weight, and summing the weights of the query words produces a relevance score used to order results.

## Key Points
- Term frequency rewards documents that mention a query word many times.
- Inverse document frequency penalizes words that appear almost everywhere and carry little discriminating power.
- The product of the two yields a per-term weight; scores accumulate across all matching query terms.
- Raw counts are usually dampened with a logarithm so that the tenth occurrence adds less than the first.
- Length normalization prevents long documents from winning purely by having more words.
- The scheme needs only the counts already kept in a postings list, making it cheap to compute at query time.

## Details
Term frequency is the count of a word inside a single document, often softened by taking its logarithm so repeated hits give diminishing returns. Inverse document frequency is computed from how many documents in the corpus contain the word at all: a rare word produces a large value, while a near-universal word produces a value close to zero. The two are multiplied per term and then added across the query.

A robust implementation guards against the edge case of a term that appears in zero documents by adding one to the document count before taking the logarithm, a smoothing constant sometimes labeled IDF_SMOOTH_EPSILON. Without it the formula would divide by zero on unseen words. Many systems also divide the final score by a document-length factor so verbose pages do not dominate simply by being long.

Because the model relies entirely on the frequencies stored alongside each posting, it pairs naturally with the structure in [[inverted-index]]: the engine reads the counts it already has rather than rescanning text. When several scoring methods are run side by side, their separate orderings can be merged with techniques such as [[reciprocal-rank-fusion]] to produce a single blended result list.
