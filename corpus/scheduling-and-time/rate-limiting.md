---
title: "Rate Limiting"
type: concept
sources: []
related:
  - "[[exponential-backoff]]"
  - "[[priority-queues]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Rate Limiting

## Overview
Rate limiting is the practice of capping how frequently a caller may perform an action over a window of time. It protects shared infrastructure from being overwhelmed, enforces fair usage among many clients, and shields downstream services from sudden floods of traffic. The most common mechanism for implementing it is the token bucket, a simple accounting trick that allows short bursts while still bounding the long-run average.

## Key Points
- Restricts the number of operations a client may issue within a defined interval.
- Defends a service against overload, abuse, and noisy-neighbor effects from a single heavy user.
- The token bucket refills at a steady rate and each request spends one token; an empty bucket means rejection or delay.
- Bucket depth controls how large a momentary burst is tolerated, separate from the sustained rate.
- A leaky bucket is the dual formulation, smoothing output to a fixed drain rate instead of allowing bursts.
- Rejected callers are typically told to slow down and retry later, often with a recommended wait.

## Details
In the token-bucket model, a counter is replenished at a constant cadence up to a maximum capacity. Each incoming request removes one unit; if none remain, the request is throttled. This cleanly separates two knobs: the refill rate sets the long-run ceiling, while the capacity sets how much of a spike the system will absorb before pushing back. Implementations frequently expose the refill cadence through a setting such as TOKEN_REFILL_RATE_PER_S so operators can tune throughput without touching code.

Accurate accounting depends on measuring elapsed time correctly, so a robust limiter reads durations from a forward-only counter rather than the wall clock; see [[monotonic-clocks]]. A clock that jumps could otherwise grant a huge refill at once or freeze the bucket entirely.

When a request is refused, the caller should not hammer the endpoint immediately. The standard cooperative response is to wait and try again on a widening schedule, which is the subject of [[exponential-backoff]]. For servers that must still serve refused-but-important work, pairing the limiter with a [[priority-queues]] arrangement lets high-value requests jump ahead once capacity returns.
