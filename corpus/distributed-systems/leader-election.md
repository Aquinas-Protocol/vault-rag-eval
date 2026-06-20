---
title: "Leader Election"
type: concept
sources: []
related:
  - "[[consensus-protocols]]"
  - "[[backpressure]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Leader Election

## Overview

Leader election is the procedure a cluster uses to pick one node as the coordinator responsible for decisions the group should not make in parallel. Designating a single leader simplifies tasks like ordering writes or assigning work, but it introduces a new problem: if the leader fails, the survivors must detect that and promote a replacement. The trickiest hazard is split brain, where two nodes each believe they are in charge and issue conflicting commands.

## Key Points

- A single coordinator avoids the chaos of many nodes trying to make the same decision at once.
- When the current leader stops responding, the remaining nodes must notice and choose a successor.
- Failover is the controlled handoff from a failed leader to a freshly elected one.
- Split brain occurs when a network partition leaves two nodes each convinced they hold authority.
- Requiring a majority vote to win an election prevents a minority partition from crowning its own leader.
- Fencing tokens stop a deposed leader from acting after a newer one has taken over.

## Details

Detection usually relies on heartbeats and timeouts. Followers expect periodic signals from the leader; when those signals stop arriving within a deadline, a follower may start a new election. Term or epoch numbers increase with each election so that messages from a stale leader can be recognized and discarded.

Avoiding split brain hinges on quorums. An aspiring leader must collect votes from a majority of the cluster before assuming the role, which guarantees that at most one candidate can win because two majorities cannot exist simultaneously. Systems often guard side effects with a monotonically increasing guard such as FENCING_EPOCH_ID=7, attached to every write so storage can reject commands stamped with an older epoch.

Leader election is effectively a specialized application of agreement and is frequently layered on top of a general [[consensus-protocols]] implementation. Once a coordinator exists, it commonly owns cluster-wide responsibilities such as admission and throttling decisions covered under [[backpressure]].
