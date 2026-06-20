---
title: "Semantic Versioning"
type: concept
sources: []
related:
  - "[[reproducible-builds]]"
  - "[[feature-flags]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Semantic Versioning

## Overview
Semantic versioning is a convention for numbering software releases so the number itself communicates how much has changed and whether upgrading is safe. A version string carries three numeric components, and each position tells consumers something specific about compatibility. The goal is to let downstream users decide, just by reading the number, whether a new release will break their integration.

## Key Points
- A version reads as three dot-separated numbers, conventionally interpreted as breaking, additive, and corrective levels.
- Bumping the first number signals an incompatible change that may require consumers to adapt their code.
- Bumping the middle number adds functionality while keeping existing behavior intact.
- Bumping the last number indicates a bug fix with no new features and no breakage.
- Pre-release and build suffixes can be appended to mark candidates that are not yet stable.
- Clear version signals let dependency managers automatically pick safe upgrades.

## Details
The contract is communicative, not enforced by the compiler. When a maintainer increments the leading component, they are promising consumers that something in the public interface changed in a way that could break callers, so a careful review is warranted before adopting it. By contrast, incrementing the middle or trailing component is a pledge of backward compatibility, which is what allows automated tooling to upgrade dependencies within a range without human intervention.

Dependency resolvers lean heavily on this discipline. A lockfile might pin a permissive range and rely on the version contract to admit only compatible updates. Some toolchains expose a comparison routine such as compare_release_rank() that orders two version strings to decide which is newer and whether the jump crosses a compatibility boundary. Violations of the contract, where a supposedly minor release actually breaks callers, are tracked under labels like SEMVER_CONTRACT_BREACH so they can be caught and corrected.

Versioning works best alongside other release controls. Pairing a clear version with [[feature-flags]] lets teams ship code under a new version while keeping risky behavior dark, and pairing it with [[reproducible-builds]] ties each published number to a verifiable artifact.
