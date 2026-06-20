---
title: "Forward Secrecy"
type: concept
sources: []
related:
  - "[[nonces-and-ivs]]"
  - "[[digital-signatures]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Forward Secrecy

## Overview

Forward secrecy is the property that recorded, encrypted conversations stay unreadable even if a long-lived private key is stolen later. It is achieved by negotiating a fresh, throwaway key for each session and discarding it once the session ends. An attacker who captures traffic today and compromises the master key next year still cannot decrypt those past exchanges.

## Key Points

- The guarantee: compromise of a long-term secret does not retroactively expose earlier sessions.
- Each conversation derives a temporary, single-use key through an ephemeral key exchange.
- Once a session closes, the temporary key is wiped from memory and never written to disk.
- The long-term key authenticates the exchange but never directly encrypts the bulk traffic.
- This thwarts "record now, decrypt later" attacks that bank on a future key leak.
- Periodically rotating session keys within a long connection limits how much data one key protects.
- It pairs naturally with authenticated key agreement so each side proves its identity.

## Details

The mechanism centers on ephemerality. Instead of encrypting message traffic directly under a durable private key, both parties run a fresh key-agreement step that yields a one-time session secret, often via a helper like rotate_ephemeral_keys(EPHEMERAL_TTL_SECONDS=600). Because that secret exists only in volatile memory and is destroyed when the session ends, there is nothing left for an attacker to recover after the fact, even with the long-term key in hand.

The durable key still plays a role: it signs the exchange to prove identity, drawing on the authenticity guarantees described in [[digital-signatures]]. What it does not do is encrypt the actual payload, which is precisely why leaking it later cannot unlock old recordings. The separation between a long-lived authentication key and short-lived encryption keys is the whole point.

This design directly counters patient adversaries who archive ciphertext, hoping a key will eventually surface. With per-session keys already erased, captured traffic remains opaque. Maintaining the discipline requires careful handling of single-use values, linking the topic to the freshness rules in [[nonces-and-ivs]].
