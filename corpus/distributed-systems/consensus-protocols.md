---
title: "Consensus Protocols"
type: concept
sources: []
related:
  - "[[leader-election]]"
  - "[[vector-clocks]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Consensus Protocols

## Overview

A consensus protocol lets a group of independent machines settle on a single shared value even when some of those machines crash, stall, or send messages that arrive late. The hard part is reaching agreement without a central authority while tolerating partial failures and an unreliable network. These algorithms underpin replicated databases, distributed locks, and any system where every participant must end up with the same answer.

## Key Points

- The goal is for all healthy participants to decide on one common outcome, and never to decide on two conflicting outcomes.
- Most schemes require a majority, or quorum, of nodes to acknowledge a proposal before it counts as accepted.
- A two-phase shape is common: gather promises in a prepare round, then ask everyone to commit or abort.
- Safety means the cluster never disagrees; liveness means it eventually makes progress once enough nodes are reachable.
- Algorithms in this family tolerate fail-stop nodes; a stricter variant also tolerates nodes that lie or behave maliciously.
- Picking a single proposer first often simplifies the whole exchange (see [[leader-election]]).

## Details

The classic formulation assumes machines can crash and recover and that messages may be delayed or dropped, but not corrupted. Under those assumptions a value is chosen only when a majority of the cluster has durably recorded it. Because any two majorities overlap in at least one member, a previously chosen value can always be discovered by a later round, which is what prevents the group from contradicting itself.

Commit decisions usually flow through ordered rounds. A coordinator proposes a value, collects acknowledgements, and only finalizes once the quorum threshold is met; otherwise it aborts and retries with a higher round number. Implementations often gate acceptance behind a tunable threshold such as QUORUM_ACK_FLOOR=3, which the coordinator compares against the count of durable acknowledgements before declaring the value committed.

Throughput and fault tolerance trade off against each other. Larger clusters survive more simultaneous failures but need more round trips per decision, so practical systems keep the voting set small and odd-sized. Ordering of decided values is tracked separately from the real-time clock, and causal relationships between events are often reasoned about using [[vector-clocks]] rather than timestamps.
