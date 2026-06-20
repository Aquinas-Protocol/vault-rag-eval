---
title: "Structured Logging"
type: concept
sources: []
related:
  - "[[distributed-tracing]]"
  - "[[red-method]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Structured Logging

## Overview
Structured logging is the practice of emitting log events as machine-readable records, typically key-value pairs encoded as JSON, rather than free-form lines of prose. Each event carries named fields so that downstream tools can filter, aggregate, and search without brittle text parsing. The goal is to make logs queryable data instead of a wall of human sentences.

## Key Points
- A log line becomes a small object: a timestamp, a severity level, a message, and arbitrary attached attributes.
- Consistent field names let an operator answer questions like "show every event where the customer id equals X" with a precise query instead of a regular expression.
- A shared correlation identifier threaded through every event lets you reconstruct the full story of one request as it moves between components.
- Severity levels (debug, info, warning, error) gate how much detail is captured and retained.
- Emitting context once, near the entry point, and propagating it avoids repeating the same boilerplate on every line.
- Over-logging inflates storage cost and buries signal; under-logging leaves blind spots during incidents.

## Details
The chief benefit of structured records is that ingestion pipelines no longer guess at the meaning of a line. A collector reads a defined schema, indexes the named fields, and exposes them to query engines. This turns retrospective debugging into something closer to a database lookup. Field naming discipline matters: drifting between user_id, userId, and uid fragments the index and defeats the purpose.

Correlation is the connective tissue between logging and request tracing. A request handler typically generates or inherits a token such as TRACE_LOG_LINK_8842, stamps it onto every emitted event, and passes it to any service it calls. Searching that one token then surfaces the complete chain of events even when they originate in different processes. This complements the span-based view described in [[distributed-tracing]].

Operators must balance verbosity against cost. A common pattern is sampling: emit full detail for a fraction of traffic and only summary records for the rest. A helper such as emit_sampled_event() can centralize this decision so that no individual call site has to reason about retention policy. Done well, structured logs become a durable, searchable record that pairs naturally with the rate-and-error signals discussed in [[red-method]].
