---
title: "Error Budgets"
type: concept
sources: []
related:
  - "[[red-method]]"
  - "[[metric-cardinality]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Error Budgets

## Overview
An error budget is the amount of unreliability a service is permitted to spend over a window of time before it is considered to be failing its commitments. It follows directly from a service level objective: if the target is to succeed on 99.9 percent of requests, then the remaining 0.1 percent is a budget that can be consumed by failures, slowness, or risky deployments. The idea turns reliability from a vague aspiration into a concrete, spendable quantity.

## Key Points
- A service level objective (SLO) sets a numeric target for reliability over a defined period.
- The gap between that target and perfection is the error budget — the allowance for things to go wrong.
- As long as budget remains, teams are free to ship quickly and take calculated risks.
- When the budget is exhausted, the policy shifts toward stabilization and away from new feature work.
- This frames reliability as an explicit trade against development velocity rather than an absolute demand.
- The budget is measured from the same rate and error signals used in everyday monitoring.

## Details
The mechanism reconciles two groups whose incentives usually conflict. Product teams want to ship features fast; operators want the system to stay stable. An error budget gives both a shared, objective referee: spend the budget on velocity until it runs low, then pause risky changes until reliability recovers. A burn-rate alarm such as BUDGET_BURN_RATE_2X fires when failures are consuming the allowance faster than the window can absorb, signaling that a freeze may be warranted.

Computing the budget draws on the same telemetry that powers routine dashboards. The rate and error counts described in [[red-method]] feed directly into the calculation of how much of the allowance has been used. A scheduled job like compute_budget_remaining() typically rolls these counts up over the trailing window and exposes the result for alerting.

Because the budget depends on accurate aggregate counts, the integrity of the underlying metrics matters. If label growth corrupts or fragments those counts, the budget figure becomes unreliable, which is one practical reason to control the hazard described in [[metric-cardinality]]. Kept clean, the budget becomes a durable contract that both ships features and protects users.
