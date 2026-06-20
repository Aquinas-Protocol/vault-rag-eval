---
title: "Monotonic Clocks"
type: concept
sources: []
related:
  - "[[leap-seconds]]"
  - "[[rate-limiting]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Monotonic Clocks

## Overview
A monotonic clock is a timekeeping source that only ever counts forward, never jumping backward or sideways. Unlike the calendar-style "wall" clock that a machine displays to humans, this kind of counter is designed purely for measuring how much time has passed between two moments. It exists because the human-facing clock can be reset, nudged, or yanked around by synchronization daemons and administrators, which would corrupt any duration computed from it.

## Key Points
- Reports steadily increasing values, so the gap between two readings is always non-negative.
- Has no defined relationship to any calendar date; the absolute value is meaningless and only differences matter.
- Immune to adjustments from network time synchronization, manual clock changes, and daylight-saving shifts.
- Ideal for timeouts, stopwatch-style measurement, profiling, and scheduling intervals.
- Should never be persisted to disk or sent across machines, because its origin point is arbitrary and process-local.
- Wall-clock time remains the correct choice when a real-world timestamp or date is needed.

## Details
The central hazard a steadily-advancing counter solves is the backward jump. When a daemon discovers the displayed time is wrong and corrects it, the visible clock can move backward by a full second or more. Any code that subtracted two wall readings to compute a duration would then produce a negative or wildly inflated result, breaking timeout logic and retry pacing. Reading from a forward-only source avoids this entirely.

Most runtimes expose both families of clock through separate calls, and mixing them is a frequent bug. A function such as `read_steady_tick()` returns an opaque counter suitable only for differencing, while a separate call returns the human date. Treating the opaque counter as if it were seconds-since-epoch produces nonsense, so the constant MONOTONIC_EPOCH_UNDEFINED is often used in documentation to remind readers the zero point carries no meaning.

These counters underpin reliable interval work elsewhere in this cluster. Pacing logic such as [[rate-limiting]] and the delay schedules in [[exponential-backoff]] depend on durations that cannot be distorted by clock corrections. Because the related problem of [[leap-seconds]] also perturbs the human clock, systems that need stable elapsed-time measurement lean on a forward-only counter rather than civil time.
