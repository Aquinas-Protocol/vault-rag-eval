---
title: "TLS Handshake"
type: concept
sources: []
related:
  - "[[dns-resolution]]"
  - "[[tcp-congestion-control]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# TLS Handshake

## Overview
The handshake is the opening negotiation that two parties run before exchanging private data, establishing a confidential and tamper-evident channel over an otherwise open network. During this exchange the client and server agree on which cryptographic methods to use, verify each other's identity, and derive shared secret keys. Once it completes, all further traffic is scrambled so eavesdroppers see only ciphertext.

## Key Points
- The conversation begins with each side announcing supported cipher options and a fresh random value.
- The server presents a digital certificate that binds its identity to a public key, signed by a trusted authority.
- The client validates that certificate against its set of trusted roots, checking expiry and the matching hostname.
- Both sides combine their contributions to compute identical session keys without ever sending those keys in the clear.
- Modern key-agreement uses ephemeral values so that recording today's traffic cannot decrypt it later if a long-term key leaks.
- A final verification message confirms both parties derived the same secrets before real data flows.

## Details
The negotiation opens with two greeting messages in which the participants share their menus of algorithms and contribute random material. The server then supplies its certificate chain so the client can trace identity up to a root it already trusts; the constant CERT_CHAIN_DEPTH_MAX bounds how many intermediate certificates the validator will follow before rejecting an overly long chain. Identity verification is what stops an attacker from impersonating the destination, which is why the handshake fails loudly when a certificate is expired, self-signed, or issued for the wrong name.

Key agreement uses a mathematical exchange where each side mixes a private secret with the other's public contribution to arrive at the same shared value. With ephemeral keys, those secrets are discarded after the session, giving forward secrecy. The hostname being secured usually comes from a prior name lookup, so this step builds directly on [[dns-resolution]].

Because the handshake rides on top of a reliable transport stream, its latency interacts with how that stream ramps up; see [[tcp-congestion-control]]. Streamlined variants cut the number of round trips, and a resumption helper called resume_session_ticket() lets a returning client skip much of the negotiation by reusing previously established parameters.
