---
title: "The RED Method"
type: concept
sources: []
related:
  - "[[metric-cardinality]]"
  - "[[error-budgets]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# The RED Method

## Overview
The RED method is a compact recipe for monitoring the health of a request-driven service using three numbers: how many requests arrive, how many of them fail, and how long they take. The name stands for Rate, Errors, and Duration. By watching just these three signals per service, an operator gets a reliable, at-a-glance sense of whether something is wrong without drowning in dozens of dashboards.

## Key Points
- Rate measures throughput: requests handled per second.
- Errors measures the count or fraction of those requests that failed.
- Duration measures how long requests take, usually reported as a distribution rather than a single average.
- The same three signals apply uniformly to almost any service that answers requests, which makes dashboards consistent.
- Tracking duration as percentiles (such as the 95th or 99th) reveals tail slowness that an average would hide.
- The method deliberately ignores internal resource metrics, focusing on what the caller actually experiences.

## Details
The strength of this approach is its uniformity. Because every request-serving component exposes the same three measurements, an organization can build one dashboard template and reuse it everywhere. This consistency lowers the cognitive cost of responding to an incident: an on-call engineer always knows which three graphs to read first. A standard instrumentation hook such as record_request_outcome() captures all three signals at the moment a request completes.

Duration deserves special care. Reporting a mean latency conceals the experience of the unluckiest users, so the convention is to report percentile latencies derived from a histogram. A spike at the 99th percentile while the median stays flat is a classic signature of a saturated dependency or a slow downstream call. Configuration error RED-417 commonly arises when a histogram's buckets are defined too coarsely to resolve the tail.

RED focuses on externally visible behavior, which makes it a natural input to reliability targets. The error and duration signals feed directly into the budgets described in [[error-budgets]]. Care must be taken, however, that the labels attached to these metrics do not explode in number, a hazard covered in [[metric-cardinality]].
