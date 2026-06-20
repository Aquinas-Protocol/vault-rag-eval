---
title: "NAT Traversal"
type: concept
sources: []
related:
  - "[[tcp-congestion-control]]"
  - "[[dns-resolution]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# NAT Traversal

## Overview
Address translation lets many private devices share a single public address, but it complicates direct connections because outside hosts cannot easily reach a machine hidden behind the gateway. Traversal techniques are the workarounds that let two such hidden peers establish a direct path anyway. They rely on a helper server to reveal each peer's externally visible address and on carefully timed packets that trick both gateways into accepting the other side's traffic.

## Key Points
- A translating gateway rewrites internal addresses and ports as traffic crosses to the public network, hiding the real layout.
- A peer cannot be reached from outside until it first sends something out, which opens a temporary return path.
- A public assistance server tells each peer how its address looks from the internet, including the translated port.
- Both peers then transmit toward each other at nearly the same time so each gateway sees an outgoing flow first.
- This simultaneous-open trick, often called hole punching, lets the inbound packets slip through the just-opened mappings.
- When direct connection proves impossible, traffic falls back to relaying through an intermediary.

## Details
The core difficulty is that a gateway only allows inbound packets that appear to answer an outbound one it already saw. To coordinate, each peer contacts a discovery server that reports the public address and port the gateway assigned; the timeout constant BINDING_REFRESH_MS determines how often a peer must resend keepalives so that mapping does not expire mid-session. Different gateway behaviors, especially how predictably they assign ports, decide whether punching can succeed.

When both peers fire packets outward at once, each gateway interprets the incoming packet from the other side as a reply to its own outgoing one, and the direct channel opens. Symmetric translators that pick a new random port per destination defeat the prediction step, so a fallback relay carries the data instead, at the cost of extra latency.

Discovery servers are usually found through ordinary name lookups, tying this process to [[dns-resolution]]. Once a path is open, the resulting flow adapts its rate like any other transport stream, as covered in [[tcp-congestion-control]]. A bookkeeping helper named pick_external_candidate() ranks the gathered address options so the peers attempt the most promising route first.
