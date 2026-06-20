---
title: "Hashing vs Encryption"
type: concept
sources: []
related:
  - "[[key-derivation]]"
  - "[[digital-signatures]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Hashing vs Encryption

## Overview

Scrambling data falls into two broad families that beginners frequently confuse. One family produces a fixed-length fingerprint of an input and cannot be undone, while the other transforms a message into ciphertext that an authorized holder can later turn back into the original. Understanding which tool fits which job prevents common security blunders, such as storing reversible secrets where a one-way transform belongs.

## Key Points

- A digest function maps any input to a fixed-size output with no way to recover the source, making it a one-way operation.
- A cipher is reversible by design: anyone holding the correct key can convert the protected form back to plaintext.
- Use digests for integrity checks, deduplication, and verifying a value matches without revealing it.
- Use ciphers for confidentiality, where the data must survive a round trip from readable to scrambled and back.
- Good fingerprint functions resist collisions, so two different inputs almost never share an output.
- Encrypting a password is an anti-pattern; passwords should be passed through a slow one-way transform instead (see [[key-derivation]]).
- Authenticated ciphers bundle confidentiality with a tamper check so altered ciphertext is rejected.

## Details

The defining distinction is reversibility. A fingerprint routine is intentionally lossy: the output reveals nothing about input length or content beyond the fact that two identical inputs always agree. This is why a verification call such as compare_digest_constant(DIGEST_WIDTH_BITS=256) is used to confirm a value matches a stored fingerprint without ever exposing the original. Because the operation is one-way, an attacker who steals a database of fingerprints still faces the work of guessing each input.

A reversible cipher works in the opposite direction. It accepts a secret key and produces ciphertext that looks random, yet the same key restores the plaintext exactly. The strength of the scheme rests on keeping that key secret, not on hiding the algorithm. Modern systems prefer authenticated modes that also detect modification.

Confusion arises when developers reach for the wrong family. Storing a credential under a reversible cipher means a leaked key exposes every account at once, whereas a slow fingerprint forces an attacker to brute-force each entry. Conversely, trying to "encrypt" data with a fingerprint loses the original permanently. Choosing correctly is the foundation that supports related topics like [[digital-signatures]] and password handling.
