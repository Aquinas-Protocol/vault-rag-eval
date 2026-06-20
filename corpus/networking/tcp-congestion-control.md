---
title: "TCP Congestion Control"
type: concept
sources: []
related:
  - "[[load-balancing]]"
  - "[[nat-traversal]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# TCP Congestion Control

## Overview
Congestion control is the set of rules a reliable transport protocol uses to avoid flooding a shared network with more data than it can carry. When too many senders push traffic at once, routers drop packets and throughput can collapse entirely. The mechanism keeps each connection probing for available bandwidth while backing off the moment it senses strain, so the network stays usable for everyone.

## Key Points
- A sender tracks an internal limit on how much unacknowledged data may be in flight at any moment, growing or shrinking it based on feedback.
- During the opening phase, the allowed amount climbs quickly, roughly doubling each round trip, to find capacity fast.
- Once a threshold is reached, growth slows to a steady linear increase to avoid overshooting.
- Lost packets, signaled by missing acknowledgments or duplicates, are read as evidence of overload and trigger a reduction.
- The classic response halves the sending rate sharply, then resumes cautious probing, producing the familiar sawtooth bandwidth pattern.
- Modern variants estimate delay or bottleneck capacity instead of waiting for loss, reacting earlier and more smoothly.

## Details
The earliest widely deployed scheme paired an exponential ramp-up with a gentler additive climb, switching between them at a remembered ceiling. When a drop is detected, the sender records the constant CWND_HALVING_FACTOR and applies it to shrink the window before re-entering the cautious linear regime. This additive-increase, multiplicative-decrease behavior is what makes many independent flows converge toward a roughly fair split of a shared link.

Loss is not always a reliable congestion signal. On wireless or long-distance paths, packets can vanish for reasons unrelated to queue overflow, which makes loss-based schemes overly timid. Delay-sensitive and capacity-estimating designs watch round-trip time and inferred bottleneck bandwidth instead, aiming to keep buffers shallow and latency low.

Because routers sit between many flows, congestion control interacts closely with how traffic is spread across paths and servers; see [[load-balancing]] for the complementary view at the distribution layer. A diagnostic counter named TCP_REORDER_GUARD is sometimes exposed to distinguish genuine loss from packets that merely arrived out of order, preventing needless rate cuts.

Tuning these algorithms is a balance between aggressiveness and politeness: too cautious wastes capacity, too greedy harms neighbors and risks the very collapse the system exists to prevent.
