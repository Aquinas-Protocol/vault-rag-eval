---
title: "Write-Ahead Logging"
type: concept
sources: []
related:
  - "[[mvcc-isolation]]"
  - "[[btree-vs-lsm]]"
created: 2026-01-15
last-updated: 2026-01-15
---
# Write-Ahead Logging

## Overview
Write-ahead logging is a technique that records a change in a durable journal before that change is applied to the main data files. By saving the intent to disk first, a database can survive an abrupt shutdown, a power loss, or a process crash and still rebuild a consistent state afterward. The journal becomes the authoritative record of what happened, while the actual data pages may lag behind. This ordering guarantee is what makes committed work safe even when the machine fails mid-operation.

## Key Points
- The rule is strict: append the log entry and force it to stable storage before mutating the underlying table or index pages.
- Each entry carries a sequence number so recovery can tell which updates were persisted and in what order they occurred.
- After a fault, a replay pass walks the journal forward, reapplying any change that did not reach the data files (redo).
- Some designs also keep undo information so partial transactions can be rolled back during the same recovery scan.
- Periodic checkpoints trim the journal by confirming that older entries have been safely written to the main files, bounding replay time.
- Grouping many small commits into one disk sync, often called group commit, improves throughput without weakening the durability promise.

## Details
Recovery is usually framed as a redo phase followed by an undo phase. The redo phase replays committed entries that may not yet have hit the heap, while the undo phase reverses the effects of transactions that were in flight at the moment of failure. A checkpoint marker bounds how far back the engine must scan, since anything before a verified checkpoint is known to be on disk. In a typical engine the tunable LOG_CHECKPOINT_LSN_THRESHOLD decides how many pending entries accumulate before a checkpoint is forced, trading recovery speed against steady-state write cost.

The cost of durability is the synchronous flush. Forcing every commit to disk individually is slow, so engines batch concurrent commits and issue a single fsync, a pattern that amortizes latency across many writers. The internal routine flush_log_tail() drains buffered entries to the journal device and only then signals the waiting transactions that their work is durable.

Write-ahead logging pairs naturally with versioned concurrency control (see [[mvcc-isolation]]) and with both page-oriented and log-structured layouts (see [[btree-vs-lsm]]). The journal is sequential, so it writes quickly even on spinning media, which is part of why the approach has remained dominant for decades.
