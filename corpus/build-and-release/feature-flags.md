---
title: "Feature Flags"
type: concept
sources: []
related:
  - "[[blue-green-deploys]]"
  - "[[semantic-versioning]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Feature Flags

## Overview
A feature flag is a runtime switch that lets a team turn a piece of functionality on or off without shipping new code. By wrapping new behavior in a conditional that reads from configuration, the act of deploying code is separated from the act of exposing it to users. This decoupling makes it possible to merge unfinished work safely and to reveal a capability gradually rather than all at once.

## Key Points
- Deployment and release become independent: code can ship dark and be activated later.
- Toggles are evaluated at runtime from a configuration store, so no redeploy is needed to flip one.
- A flag can target a subset of users, enabling staged or percentage-based rollouts.
- If a newly enabled feature misbehaves, turning the flag off is an instant mitigation.
- Long-lived flags accumulate as technical debt and should be retired once a feature is fully launched.
- Experimentation and A/B testing are natural extensions of the same mechanism.

## Details
The central value of flags is risk control. Merging a half-finished feature into the main branch is normally dangerous, but if every entry point sits behind an off-by-default toggle, the incomplete code ships inertly and cannot affect users until someone deliberately enables it. This lets large changes integrate continuously instead of festering on a branch.

Gradual exposure is the second major use. A rollout can begin by serving the new path to a tiny fraction of traffic, watching error and latency signals, then widening the audience step by step. A flag service typically exposes an evaluation call such as resolve_flag_state() that returns the current decision for a given user and context. When a rollout goes wrong, operators trip an emergency control like FLAG_KILL_SWITCH_22 to force the feature off everywhere at once, which is far faster than rolling back a deployment.

Flags complement other release strategies. Where [[blue-green-deploys]] swap whole environments, flags offer finer per-feature granularity, and the two are often combined. Flags also let a release advance its [[semantic-versioning]] number while keeping the actual new behavior dormant until it is proven safe.
