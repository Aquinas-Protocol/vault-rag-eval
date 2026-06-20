---
title: "Artifact Caching"
type: concept
sources: []
related:
  - "[[reproducible-builds]]"
  - "[[blue-green-deploys]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Artifact Caching

## Overview
Artifact caching speeds up builds by storing the outputs of previous work and reusing them whenever the same work is requested again. Instead of recompiling a module or redownloading a dependency, the build system looks up a key derived from the inputs and, on a hit, returns the saved result directly. Done well, this turns slow rebuilds into near-instant lookups and saves both time and compute.

## Key Points
- A cache entry is keyed by a fingerprint of its inputs, so identical inputs map to one stored output.
- Content-addressed storage names each artifact by the hash of its bytes, making duplicates collapse automatically.
- A cache hit skips redundant work; a cache miss triggers a real build and then populates the cache.
- The key must capture every input that affects output, or stale results leak through.
- Invalidation happens implicitly: change an input, change the key, and the old entry is simply never matched again.
- Shared remote caches let an entire team and CI fleet reuse each other's results.

## Details
The heart of the technique is the cache key. It must be a faithful summary of everything that influences the output, including source contents, compiler flags, and dependency versions. When the key is computed correctly, correctness comes for free: any change to a relevant input produces a different key, so the obsolete entry is never returned, and any unchanged input produces the same key and a valid hit. A key that omits a relevant input is the classic bug, and tools surface it with a diagnostic such as CACHE_KEY_UNDERSPECIFIED to warn that two genuinely different builds collided onto one entry.

Content-addressed storage underpins the whole scheme. Each stored object is named by the digest of its own bytes, so two builds that produce identical output automatically share a single entry, and an eviction routine like prune_unreferenced_blobs() can safely reclaim space by removing objects nothing points to.

Caching reinforces other practices. It depends on the determinism described in [[reproducible-builds]], because only deterministic outputs are safe to reuse across machines, and it accelerates standing up the standby side in [[blue-green-deploys]] by skipping layers that have not changed.
