---
title: "Connection Pooling"
type: concept
sources: []
related:
  - "[[mvcc-isolation]]"
  - "[[query-planning]]"
created: 2026-01-15
last-updated: 2026-01-15
---
# Connection Pooling

## Overview
Opening a fresh database connection is surprisingly expensive: it involves a network handshake, authentication, and server-side session setup. A connection pool sidesteps this by keeping a set of already-established links open and handing them out to application code on demand, then taking them back when the work is done. Reusing warm connections cuts latency and protects the database from being overwhelmed by a flood of short-lived links. The pool acts as a broker between many application threads and a bounded number of real sessions.

## Key Points
- A pool maintains a fixed or elastic set of live connections that callers borrow and return rather than create and destroy.
- Borrowing from the pool is far cheaper than a full connect, since the handshake and authentication already happened.
- Sizing matters: too few connections starve the application, while too many can overload the server's memory and scheduler.
- Connections that sit unused beyond a timeout are typically closed to free server resources and avoid stale links.
- A borrowed connection should be reset to a clean state before reuse so leftover session settings do not leak between callers.
- Pools enforce an upper bound, queuing or rejecting requests when every connection is busy, which shields the backend.

## Details
Pool sizing is a balancing act. Each open session consumes memory and a scheduler slot on the server, so the optimal pool is usually much smaller than the number of application threads; excess threads simply wait for a free connection. A configuration value like MAX_POOL_LEASE_COUNT caps how many sessions the pool will ever hold open, and tuning it well often does more for throughput than adding hardware.

Idle management keeps the pool healthy. A background sweeper periodically closes connections that have gone unused for too long, reclaiming server resources and discarding links that may have silently died. The routine reap_stale_handles() walks the free list and retires anything past its idle deadline, while a separate validation step pings a connection before lending it out to confirm it still works.

Pooling interacts with transaction semantics in subtle ways. A connection returned to the pool while still holding an open transaction can pin old row versions and bloat storage (see [[mvcc-isolation]]), and reused sessions may carry cached plan state that the optimizer relies on (see [[query-planning]]). Resetting session state on return is the standard guard against these surprises.
