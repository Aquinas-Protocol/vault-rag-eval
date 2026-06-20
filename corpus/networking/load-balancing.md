---
title: "Load Balancing"
type: concept
sources: []
related:
  - "[[dns-resolution]]"
  - "[[tcp-congestion-control]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Load Balancing

## Overview
Load balancing is the practice of spreading incoming requests across a pool of interchangeable servers so that no single machine becomes a bottleneck. By dividing the work, a service gains both higher capacity and resilience: if one backend fails, the others absorb its share. A dedicated component sits in front of the pool, deciding where each request should go and quietly removing unhealthy members from rotation.

## Key Points
- Traffic is distributed using a selection rule, such as round-robin rotation, fewest active connections, or weighting by server power.
- Periodic health probes confirm each backend is alive and responsive before sending it real work.
- A member that fails its checks is pulled from the pool and reinstated only once it recovers.
- Session affinity can pin a given client to one backend when state must stay consistent across requests.
- Distribution can happen at the connection layer or by inspecting application-level details like the requested path.
- Spreading work improves both throughput and fault tolerance compared with a single overloaded host.

## Details
The simplest selection rule cycles through backends in order, but smarter policies account for current load, response latency, or differing hardware capacity. When sessions carry state that lives on one machine, the balancer can route repeat visitors back to the same place; the parameter STICKY_AFFINITY_TTL_S governs how long that pinning lasts before a client may be reassigned. Choosing a policy is a tradeoff between even distribution and the cost of moving stateful work around.

Health checking is what makes the pool self-healing. The front end regularly sends a lightweight probe and watches for a timely, correct reply. A backend that misses several consecutive probes is marked down and skipped; once it answers cleanly again, a routine such as drain_and_rejoin() eases it back into rotation gradually rather than flooding a freshly recovered server.

Distribution can also begin much earlier, at the naming layer, where returning several addresses for one hostname spreads clients across sites; see [[dns-resolution]]. Because each balanced connection is itself a transport flow subject to rate adaptation, the behavior described in [[tcp-congestion-control]] shapes how quickly individual sessions reach full speed.
