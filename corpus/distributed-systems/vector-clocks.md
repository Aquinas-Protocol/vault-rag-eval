---
title: "Vector Clocks"
type: concept
sources: []
related:
  - "[[consensus-protocols]]"
  - "[[idempotency-keys]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Vector Clocks

## Overview

A vector clock is a bookkeeping device that lets distributed processes figure out which events happened before which others, without trusting any single synchronized wall clock. Each participant keeps a small array of counters, one slot per process, and bumps its own slot every time something happens locally. By comparing two of these arrays, a system can tell whether one event caused another, whether they are concurrent, or whether they are unrelated.

## Key Points

- Physical timestamps drift between machines, so they cannot reliably order events across a cluster.
- Each process holds a tally of counters and increments its own entry on every local action.
- When a message is sent, the sender's whole counter array travels with it; the receiver merges by taking the element-wise maximum.
- Comparing two arrays reveals one of three relationships: strictly earlier, strictly later, or simultaneous and independent.
- Concurrent updates that neither precede the other signal a potential conflict that must be reconciled.
- The technique captures the "happened-before" relation that pure timestamps miss.

## Details

The core idea is causality, not real time. If every counter in array A is less than or equal to the matching counter in array B, and at least one is strictly smaller, then the event tagged A definitely happened before the event tagged B. If neither array dominates the other, the two events are concurrent and the application must decide how to merge them.

Merging on receipt is mechanical. A receiving process walks both arrays and stores the larger value in each position, then increments its own slot to mark the receive event. Many implementations expose this step as a helper such as merge_causal_history(local, incoming) so that replicas converge on a consistent view of ordering after exchanging updates.

Vector clocks are widely used in eventually consistent stores to detect write conflicts and in causal-ordering layers that sit beneath stronger guarantees like those provided by [[consensus-protocols]]. They pair naturally with deduplication strategies, because recognizing that two writes are causally identical is closely related to recognizing duplicate requests handled by [[idempotency-keys]].
