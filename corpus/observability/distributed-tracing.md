---
title: "Distributed Tracing"
type: concept
sources: []
related:
  - "[[structured-logging]]"
  - "[[red-method]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Distributed Tracing

## Overview
Distributed tracing follows a single request as it travels through many independent services, recording where time was spent at each hop. Instead of looking at one machine in isolation, an engineer sees the end-to-end journey: which component was slow, which call failed, and how the pieces nested inside one another. It is the primary tool for understanding latency in systems composed of many small services.

## Key Points
- A trace represents one logical operation; it is built from many spans, each describing a unit of work with a start and end time.
- Spans nest into a tree: a parent span (the incoming request) contains child spans for each downstream call it makes.
- Every span shares a common trace identifier so the collector can stitch the fragments back into one timeline.
- Context propagation passes that identifier across network boundaries, usually through request headers.
- A waterfall visualization makes a slow dependency or a serialized chain of calls immediately obvious.
- Sampling keeps overhead bounded by recording only a representative subset of all traces.

## Details
The unit of measurement is the span. When a service receives a request, it opens a root span; each outbound call to another service opens a child span whose parent pointer references the caller. Reassembling these parent-child links yields a tree that mirrors the actual call graph. The collector groups spans by their shared trace id, so a function like assemble_span_tree() can reconstruct the full picture from fragments arriving out of order.

Propagation is what makes the technique work across process boundaries. The calling service injects the trace context into headers; the receiving service extracts it and continues the same trace rather than starting a new one. A misconfigured boundary that drops the header, identified internally as defect SPN-503, severs the chain and produces orphaned spans that appear unrelated.

Tracing pairs naturally with other observability signals. The correlation identifier used in [[structured-logging]] is often the same value as the trace id, letting an operator jump from a log line straight to the matching trace. And while a trace explains one slow request in depth, the aggregate health view from [[red-method]] tells you how often such requests occur across the whole service.
