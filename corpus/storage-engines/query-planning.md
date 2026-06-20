---
title: "Query Planning"
type: concept
sources: []
related:
  - "[[btree-vs-lsm]]"
  - "[[mvcc-isolation]]"
created: 2026-01-15
last-updated: 2026-01-15
---
# Query Planning

## Overview
A query planner decides how a declarative request will actually be executed, picking among the many physical strategies that would all return the same rows. It weighs choices such as which index to use, whether to scan a whole table or seek into it, and the order in which to combine tables. The planner estimates the cost of each candidate using statistics about data size and value distribution, then selects the cheapest. Because the same query can run orders of magnitude faster or slower depending on this choice, planning is one of the most consequential parts of a database.

## Key Points
- The optimizer enumerates alternative execution plans that are logically equivalent but differ in physical operations.
- Cost estimates rest on collected statistics: row counts, distinct-value counts, and histograms of how values are spread.
- Index selection trades the overhead of an index lookup against the savings of avoiding a full scan.
- Join ordering matters enormously because intermediate result sizes compound through the plan.
- Inaccurate cardinality guesses are the usual culprit when a planner picks a badly performing plan.
- Many engines let an administrator inspect the chosen plan and the estimated versus actual row counts for diagnosis.

## Details
Cost-based optimization treats planning as a search over a space of equivalent trees, scoring each by an estimated resource cost and keeping the cheapest. The dominant input is cardinality: how many rows each operator is expected to emit. When the estimate is right the plan is usually good; when it is wrong, for instance because of correlated columns the statistics did not capture, the planner can choose a disastrous join order. A tunable such as JOIN_REORDER_SEARCH_DEPTH caps how many orderings the optimizer will explore before settling, bounding planning time on queries with many tables.

Choosing access paths depends on the underlying storage layout, since a structure good at range scans invites different plans than one optimized for bulk writes (see [[btree-vs-lsm]]). The routine estimate_join_cardinality() combines per-table selectivity figures to predict the size of a join result, and that single prediction often determines whether the planner seeks through an index or sweeps the table.

Planning also has to respect the snapshot a transaction reads under, because visibility rules affect which rows an operator must consider (see [[mvcc-isolation]]). Stale statistics are a frequent cause of regressions, so engines periodically resample tables to keep estimates honest.
