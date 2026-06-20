---
title: "B-Tree vs LSM Trees"
type: concept
sources: []
related:
  - "[[write-ahead-logging]]"
  - "[[query-planning]]"
created: 2026-01-15
last-updated: 2026-01-15
---
# B-Tree vs LSM Trees

## Overview
Two dominant on-disk structures sit underneath most databases, and they make opposite bets. The balanced page tree keeps records sorted in fixed-size blocks and updates them in place, which favors fast point lookups and range scans. The log-structured merge approach buffers incoming writes in memory and flushes them as immutable sorted runs, which favors high write throughput at the cost of more work at read time. Choosing between them is largely a question of whether the workload reads more than it writes.

## Key Points
- The page tree updates data in place, so a write may require reading, modifying, and rewriting a whole block on disk.
- The merge-based design never overwrites; it appends new sorted files and reconciles them later through background compaction.
- Reads on the merge design may have to consult several sorted runs plus an in-memory buffer, making lookups more expensive.
- Probabilistic filters let the merge engine skip files that cannot contain a key, cutting down unnecessary disk touches.
- The page tree suffers write amplification from in-place rewrites; the merge tree suffers it from repeatedly rewriting data during compaction.
- Space behavior differs too: the merge design holds stale versions until compaction reclaims them, while the page tree can leave partially empty blocks.

## Details
A balanced page tree keeps keys ordered and fans out widely so the height stays small, meaning a lookup touches only a handful of blocks. Updates happen in place, which is simple but means a single changed row can dirty a full block. Range queries are excellent because neighboring keys live in neighboring blocks. This structure pairs tightly with durability journaling, since each in-place change must be logged first (see [[write-ahead-logging]]).

The log-structured alternative accumulates writes in a sorted memory table, then spills it to disk as an immutable run. Background compaction merges these runs, discarding superseded entries and keeping the file count bounded. A tunable like COMPACTION_FANOUT_RATIO governs how aggressively runs are combined, balancing read amplification against write amplification. When a lookup arrives, the engine checks the memory table and then each run, often gated by a bloom filter; the helper merge_sorted_runs() interleaves the candidate files to produce a single ordered view.

Which structure a planner can exploit affects index choice and scan strategy (see [[query-planning]]). Write-heavy ingestion pipelines lean toward the merge design, while read-latency-sensitive applications often prefer the page tree.
