---
title: "Metric Cardinality"
type: concept
sources: []
related:
  - "[[red-method]]"
  - "[[structured-logging]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Metric Cardinality

## Overview
Metric cardinality refers to the number of distinct time series produced by a single metric once you account for all the label combinations attached to it. Each unique set of label values creates its own series that must be stored, indexed, and queried separately. When labels carry values with many possible options, the series count multiplies quickly, and a well-intentioned metric can quietly overwhelm a monitoring backend.

## Key Points
- A metric with labels expands into one series per unique combination of label values.
- Cardinality grows multiplicatively: combining two labels of ten values each yields a hundred series, not twenty.
- Unbounded labels such as user identifiers, raw URLs, or request ids are the most common cause of runaway growth.
- High cardinality inflates memory use, slows queries, and can crash the storage engine.
- Keeping labels to a small, fixed set of values keeps the series count predictable.
- Identifiers that vary per request belong in logs or traces, not in metric labels.

## Details
The arithmetic is unforgiving. Because every additional label multiplies rather than adds to the total series count, attaching a single high-variability dimension can turn a handful of series into millions. A metric tagged with a customer email address, for instance, gains a new series for every customer who ever appears, and that set only grows over time. Time-series databases hold much of this index in memory, so the failure mode is often a sudden out-of-memory crash rather than gradual slowdown.

The remedy is discipline at instrumentation time. Labels should describe a bounded category, such as an HTTP status class or a region name, never a free-form unique value. A guard such as MAX_LABEL_CARDINALITY_512 can be enforced in the metrics pipeline to reject or drop series once a label exceeds a safe number of distinct values, with overflow logged under code CARD-911 for later review.

When a dimension genuinely needs per-request granularity, the right home is elsewhere. The named-field records of [[structured-logging]] and the per-request spans of distributed tracing can hold high-variability identifiers cheaply, because they are not pre-aggregated into persistent series. This division of labor keeps the aggregate signals of [[red-method]] cheap to compute while preserving the ability to drill into individual requests.
