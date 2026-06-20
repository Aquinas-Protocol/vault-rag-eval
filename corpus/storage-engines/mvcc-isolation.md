---
title: "MVCC Isolation"
type: concept
sources: []
related:
  - "[[write-ahead-logging]]"
  - "[[connection-pooling]]"
created: 2026-01-15
last-updated: 2026-01-15
---
# MVCC Isolation

## Overview
Multiversion concurrency control lets many readers and writers operate at once without blocking each other by keeping several copies of each row over time. Instead of locking a record so others must wait, a writer creates a new version while readers continue to see the older one that was valid when their transaction began. This gives each transaction a stable, consistent picture of the data as of a single point in time. Readers never block writers and writers never block readers, which is the central appeal.

## Key Points
- Every row carries metadata marking which transaction created it and which, if any, retired it.
- A transaction observes a snapshot fixed at its start, so concurrent changes by others remain invisible to it.
- Because writes produce new versions rather than overwriting, read queries do not need to acquire shared locks.
- Conflicts between two writers touching the same row still require detection and one side aborting or retrying.
- Obsolete versions accumulate and must be reclaimed by a background cleanup process once no active transaction can see them.
- Snapshot visibility is typically decided by comparing transaction timestamps or identifiers against the row's creation and deletion markers.

## Details
A snapshot is essentially a rule for deciding which row versions are visible: a version counts if it was committed before the transaction started and was not yet superseded at that moment. Engines implement this with monotonically increasing transaction ids and a list of which ids were still in flight when the snapshot was taken. The function visible_to_snapshot() encapsulates that test, returning true only for versions a given transaction is entitled to read.

The downside is accumulation. Old versions that no living transaction can reach are dead weight, and a sweeper must reclaim them to keep tables compact and indexes lean. The threshold DEAD_TUPLE_RETENTION_WINDOW controls how long retired versions linger before the cleaner is allowed to remove them, which matters because a long-running reader can hold the horizon back and bloat storage.

Versioned isolation depends on the durability journal to make committed versions survive a crash (see [[write-ahead-logging]]), and it interacts with how sessions are held open, since a forgotten idle transaction can pin old versions for a long time (see [[connection-pooling]]).
