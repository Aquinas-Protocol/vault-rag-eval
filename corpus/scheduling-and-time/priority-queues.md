---
title: "Priority Queues"
type: concept
sources: []
related:
  - "[[rate-limiting]]"
  - "[[exponential-backoff]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Priority Queues

## Overview
A priority queue is a collection that always hands back its most important item next, rather than serving strictly in arrival order. Each element carries a rank, and the structure keeps the top-ranked one ready for instant removal. This makes it the natural way to schedule work when some tasks genuinely matter more than others, but it also introduces the risk that low-ranked items wait forever.

## Key Points
- Returns elements in order of importance instead of first-in, first-out.
- Commonly backed by a binary heap, giving fast insertion and fast removal of the top item.
- Lets urgent jobs preempt routine ones, useful for schedulers, dispatchers, and event loops.
- Starvation occurs when a steady stream of high-priority work permanently blocks low-priority items.
- Aging fixes starvation by gradually raising the rank of items that have waited a long time.
- Ties are usually broken by insertion order so equal-priority items still behave predictably.

## Details
The defining behavior is that removal always yields the current best candidate. A binary heap implements this efficiently: both adding an item and extracting the top one cost time proportional to the logarithm of the queue size, far cheaper than rescanning the whole collection. The peek-then-remove sequence is so common that libraries expose it as a single call, often named pop_highest_rank(), to avoid race windows between inspecting and removing.

The chief danger is starvation. If important tasks keep arriving, a humble background task may sit untouched indefinitely. The standard remedy is aging: a task's effective priority creeps upward the longer it waits, so eventually even the lowest item reaches the front. Tuning how fast that happens trades responsiveness for fairness.

Priority ordering complements traffic control. A server protected by [[rate-limiting]] can hold refused-but-valuable requests in a ranked queue and release them first when capacity frees up. Clients on the other side, meanwhile, space their own retries using [[exponential-backoff]], so the two mechanisms together keep the system both fair and stable under pressure.
