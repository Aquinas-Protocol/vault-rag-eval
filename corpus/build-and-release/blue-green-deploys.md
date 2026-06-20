---
title: "Blue-Green Deploys"
type: concept
sources: []
related:
  - "[[feature-flags]]"
  - "[[artifact-caching]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Blue-Green Deploys

## Overview
A blue-green deployment keeps two complete production environments side by side, with only one of them serving live traffic at any moment. New code is installed and warmed up on the idle environment while the active one keeps handling requests untouched. Releasing then becomes a matter of redirecting traffic from the old environment to the new one, and rolling back is just as simple in reverse.

## Key Points
- Two full environments exist in parallel: one live, one standing by.
- The new version is deployed to the inactive side and validated before any user reaches it.
- Cutover flips a router or load balancer to point at the freshly prepared environment.
- Switchover is near-instant, so users experience little or no downtime.
- Rollback means pointing traffic back at the previous environment, which is still intact.
- The cost is running double the infrastructure during the transition window.

## Details
The defining trait is that the candidate release is fully provisioned and exercised before it ever takes production load. Smoke checks, health probes, and warmup requests run against the standby environment while real users continue hitting the current one. Only after the new side passes its checks does an operator promote it. Promotion is commonly driven by a single control such as SWAP_ACTIVE_SLOT that updates the routing layer to send all incoming traffic to the previously idle environment.

Recovery is the headline benefit. Because the prior environment is left fully running rather than torn down, a regression discovered after cutover can be reverted by flipping the router back, often in seconds. Some systems gate this behind a confirmation step like BLUEGREEN_PROMOTE_CONFIRM to prevent an accidental or premature switch.

The pattern trades infrastructure cost for safety and speed, since two environments must be paid for during the overlap. It composes well with other techniques: standing up the standby side benefits from fast [[artifact-caching]] so identical layers need not be rebuilt, and combining it with [[feature-flags]] adds per-feature control on top of the coarse environment swap.
