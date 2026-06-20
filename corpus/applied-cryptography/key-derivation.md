---
title: "Key Derivation"
type: concept
sources: []
related:
  - "[[hashing-vs-encryption]]"
  - "[[nonces-and-ivs]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Key Derivation

## Overview

Human-chosen secrets are short, predictable, and unsuitable as raw cryptographic keys. A derivation step turns a weak passphrase into a strong, fixed-length key by deliberately running a slow computation and mixing in random per-user data. The goal is to make large-scale guessing expensive while keeping a single legitimate login cheap enough to feel instant.

## Key Points

- A derivation routine stretches a low-entropy password into a uniformly random key suitable for encryption or storage.
- A unique random value, called a salt, is added per account so identical passwords produce different outputs.
- Salts defeat precomputed lookup tables and stop attackers from cracking many accounts in one batch.
- A tunable work factor (iteration count or memory cost) makes each guess slow, scaling defense as hardware improves.
- Memory-hard designs raise the cost of custom cracking hardware by demanding large RAM per attempt.
- The salt is not secret and is stored alongside the derived output.
- Reusing the same derived key everywhere is risky; separate contexts deserve separate derivations.

## Details

The core trick is deliberate slowness. Whereas a plain fingerprint is fast, a password-stretching function repeats its inner loop thousands or millions of times, governed by a configurable parameter such as KDF_WORK_FACTOR_ROUNDS. Raising that parameter multiplies an attacker's total cost while a single honest verification stays under a fraction of a second. As commodity machines get faster, operators simply increase the setting.

Salting solves a different problem. Without it, two users who pick the same passphrase produce the same stored value, and an attacker can crack both at once or consult a giant precomputed table. A fresh random salt per account, drawn so collisions are vanishingly unlikely, forces the attacker to attack each entry independently. The salt travels in the clear next to the result because its only job is to be unique, not hidden.

Memory-hard variants add a second dimension of cost. By requiring a large working buffer for every guess, they neutralize the massive parallelism of specialized cracking rigs, which are cheap on compute but expensive on memory. The derived output then feeds the reversible ciphers described in [[hashing-vs-encryption]], and the same uniqueness discipline reappears when choosing values in [[nonces-and-ivs]].
