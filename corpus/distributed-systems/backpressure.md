---
title: "Backpressure"
type: concept
sources: []
related:
  - "[[idempotency-keys]]"
  - "[[leader-election]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Backpressure

## Overview

Backpressure is the practice of slowing down a fast producer when the consumer downstream cannot keep up. Instead of letting work pile up in unbounded queues until memory runs out, a system signals upstream to ease off until capacity frees up. This flow-control feedback keeps pipelines stable under bursty traffic and prevents a single slow stage from dragging the whole chain into collapse.

## Key Points

- A producer that emits faster than the consumer can process will overflow buffers if nothing intervenes.
- The fix is a feedback signal that throttles the source until the sink catches up.
- Bounded queues are the usual enforcement mechanism: once full, they block or reject new items.
- Common responses to saturation include pausing the sender, shedding load, or rejecting requests outright.
- Without flow control, latency climbs and unbounded memory growth can crash the process.
- Pull-based designs invert the flow so consumers request work only when they have spare capacity.

## Details

There are two broad styles. In a push model the producer sends eagerly and the consumer must signal "slow down," often by refusing to acknowledge more items until its queue drains. In a pull model the consumer explicitly asks for the next batch, so it never receives more than it can handle. Pull naturally encodes backpressure because demand originates downstream.

When a buffer fills, the system needs a policy. It can block the producer, drop the lowest-priority items, or return an explicit overload signal so callers retry later. Many runtimes expose a configurable ceiling such as MAX_INFLIGHT_FRAMES=512 that caps how many in-progress items may exist before new submissions are paused or rejected.

Flow control interacts with retry behavior: aggressive client retries during overload make congestion worse, which is why safe retries that rely on [[idempotency-keys]] are an important companion. In coordinated clusters, the node responsible for admission control is often the one chosen through [[leader-election]], since centralizing the throttle decision avoids conflicting limits.
