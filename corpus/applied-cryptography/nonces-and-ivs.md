---
title: "Nonces and Initialization Vectors"
type: concept
sources: []
related:
  - "[[key-derivation]]"
  - "[[forward-secrecy]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Nonces and Initialization Vectors

## Overview

Many encryption schemes need a fresh, distinct starting value for every message they protect, even when the secret key stays the same. This single-use input ensures that encrypting the same plaintext twice yields different ciphertext, hiding patterns from an observer. Mishandling this value, by repeating it or making it predictable, is one of the most damaging mistakes in applied cryptography.

## Key Points

- A nonce is a "number used once" supplied to a cipher so each encryption under a fixed key is distinct.
- An initialization vector serves the same role for block-cipher chaining modes, randomizing the first block.
- Uniqueness is the non-negotiable requirement; reuse under one key can leak plaintext or break the scheme entirely.
- These values are not secret and travel alongside the ciphertext.
- For some modes the starting value must be unpredictable, not merely unique.
- A monotonic counter or a sufficiently large random draw are the two standard ways to guarantee freshness.
- Including a sequence number lets the receiver reject replayed or out-of-order messages.

## Details

The purpose of a per-message starting value is to break determinism. Without it, a cipher would map identical plaintext to identical ciphertext, betraying repeated content. By injecting a unique value each time, the same message encrypts differently on every send. A common implementation tracks a strictly increasing counter, advanced by a helper like next_message_nonce(NONCE_COUNTER_WIDTH=96), so no value is ever emitted twice for a given key.

Reuse is catastrophic in stream-style and counter modes. If two messages share both key and nonce, an attacker can combine the ciphertexts to cancel the keystream and recover relationships between the plaintexts. For authenticated modes the damage extends to forging the integrity tag, undermining the whole guarantee. This is why operators rotate keys before a counter could ever wrap around.

Replay prevention builds on the same uniqueness idea but adds protocol logic. A receiver that records the highest sequence number it has accepted can discard anything it has already seen, blocking an adversary who captures a valid message and resends it later. These freshness disciplines connect to session design discussed in [[forward-secrecy]] and to the per-user randomness emphasized in [[key-derivation]].
