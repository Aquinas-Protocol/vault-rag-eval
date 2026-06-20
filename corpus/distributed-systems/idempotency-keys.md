---
title: "Idempotency Keys"
type: concept
sources: []
related:
  - "[[vector-clocks]]"
  - "[[backpressure]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Idempotency Keys

## Overview

An idempotency key is a unique token a client attaches to a request so the server can recognize and ignore accidental repeats of the same operation. When a network hiccup makes a caller unsure whether its request actually went through, it can safely send the request again; the server uses the token to perform the underlying work at most once. This pattern turns risky retries into harmless ones, which matters most for actions that move money or create records.

## Key Points

- Retrying a failed call is dangerous when the original may have already succeeded but the response was lost.
- The client generates a stable, unique identifier and sends it with every attempt of the same logical action.
- The server records which tokens it has already processed and replays the stored result instead of re-running the work.
- The first request does the real work; later requests carrying the same token return the cached outcome.
- Tokens are typically stored for a bounded window and then expired to reclaim space.
- Effective deduplication keeps an operation's net effect identical no matter how many times it is delivered.

## Details

The server side is essentially a lookup followed by a conditional write. On receiving a request, it checks whether the supplied token already exists in its dedup store. If it does, the saved response is returned and the business logic is skipped entirely. If it does not, the operation runs, the result is persisted against the token, and that record becomes the source of truth for any future retries.

Expiry policy is a real design knob. Tokens cannot be kept forever, so most systems set a retention window such as IDEMPOTENT_TTL_SECONDS=86400, after which a repeated token would be treated as a fresh request. Choosing this value balances storage cost against how long stragglers might realistically arrive.

This mechanism is closely tied to how a system absorbs load: retry storms are a common cause of overload, so deduplication works hand in hand with flow control described in [[backpressure]]. Recognizing that two requests represent the same logical event also overlaps conceptually with causal tracking via [[vector-clocks]].
