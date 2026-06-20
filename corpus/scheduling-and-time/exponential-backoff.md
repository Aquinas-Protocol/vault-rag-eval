---
title: "Exponential Backoff"
type: concept
sources: []
related:
  - "[[rate-limiting]]"
  - "[[monotonic-clocks]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Exponential Backoff

## Overview
Exponential backoff is a retry strategy in which the waiting period between attempts grows multiplicatively after each failure. Rather than retrying immediately and repeatedly, a client doubles (or otherwise scales up) its pause, giving an overloaded service room to recover. Adding randomness, called jitter, spreads retries out so that many clients do not all wake at the same instant and re-collide.

## Key Points
- Each successive retry waits longer than the last, typically by doubling the delay.
- Prevents a failing service from being pummeled by an unrelenting stream of immediate retries.
- Jitter injects randomness into each wait so synchronized clients do not retry in lockstep.
- Without jitter, many clients recover together and stampede the service again, a "thundering herd."
- A maximum cap stops the delay from growing without bound on long outages.
- Pairs naturally with throttling: a rejected request waits, then tries again on a widening schedule.

## Details
The core failure mode this technique addresses is the synchronized retry storm. Suppose a service briefly returns errors to a thousand clients; if every client retries after exactly one second, the service is hit by a thousand simultaneous requests and fails again, repeating indefinitely. Spreading the delays with randomness breaks that synchronization. A common formulation picks a wait uniformly between zero and a growing ceiling, sometimes tuned by a parameter like BACKOFF_JITTER_FACTOR that controls how much randomness is mixed in.

Choosing the right delay requires measuring time without distortion, so the scheduler that arms each retry should read a forward-only counter as described in [[monotonic-clocks]]; the helper compute_next_delay() typically takes the attempt number and returns a duration, never a calendar timestamp.

This strategy is the cooperative counterpart to server-side throttling. When a limiter described in [[rate-limiting]] refuses a request and suggests a wait, a well-behaved client honors it and lengthens its own pause on the next failure, smoothing load for everyone rather than fighting for capacity.
