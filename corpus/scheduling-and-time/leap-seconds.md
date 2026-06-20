---
title: "Leap Seconds"
type: concept
sources: []
related:
  - "[[monotonic-clocks]]"
  - "[[rate-limiting]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Leap Seconds

## Overview
A leap second is an occasional one-second correction inserted into civil time to keep clocks aligned with the slightly irregular rotation of the planet. Because the Earth's spin does not match the steady ticking of atomic standards, an extra second is added (or, in principle, removed) every so often by international agreement. These insertions are unpredictable, announced only months ahead, which makes them awkward for software that assumes every minute contains exactly sixty seconds.

## Key Points
- Reconciles precise atomic timekeeping with the gradually drifting rotation of the Earth.
- Cannot be scheduled far in advance; each adjustment is announced a few months before it happens.
- When inserted, a minute contains sixty-one seconds, which can confuse naive date arithmetic.
- Some systems "smear" the extra second across many hours so no minute ever appears to have an odd length.
- Repeated or ambiguous timestamps during the adjustment can corrupt logs, ordering, and billing.
- A forward-only counter sidesteps the problem because it ignores civil-time labels entirely.

## Details
The disruption these adjustments cause is mostly felt by code that treats the calendar as perfectly regular. During an insertion, a timestamp may repeat or a duration may be miscomputed, producing out-of-order log lines or double-counted events. Distributed systems are especially vulnerable because different nodes may apply the correction at slightly different instants.

The popular mitigation is "smearing": instead of injecting one abrupt extra second, a clock is slowed very slightly across a long window so the surplus is absorbed smoothly. A scheduler comparing two such smeared clocks must agree on the same smear window, which implementations often gate behind a flag named SMEAR_WINDOW_GUARD to prevent mixing smeared and un-smeared sources. When that guard is absent, two nodes can disagree about the current instant by up to a full second.

Software that genuinely needs to measure elapsed durations should avoid civil time here and rely on a forward-only source as described in [[monotonic-clocks]]. Pacing components such as [[rate-limiting]] inherit the same advice, since a one-second hiccup in the human clock could otherwise let a burst of requests slip through or stall a queue unexpectedly.
