---
title: "Digital Signatures"
type: concept
sources: []
related:
  - "[[hashing-vs-encryption]]"
  - "[[forward-secrecy]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# Digital Signatures

## Overview

A digital signature lets a recipient confirm both who authored a message and that nobody altered it in transit. It relies on a key pair: the author signs with a private key kept secret, and anyone can verify using the matching public key. This asymmetry is what makes signatures different from a shared-secret tag, since verification requires no access to the signer's secret.

## Key Points

- Signing proves authenticity (the message came from the holder of the private key) and integrity (it was not modified).
- The signer uses a private key; verifiers use the freely distributable public key.
- In practice the message is first reduced to a fixed-length fingerprint, then that digest is signed.
- A valid signature on tampered content fails verification, exposing any change.
- Non-repudiation means the signer cannot plausibly deny having produced the signature.
- The public key must be bound to an identity, usually via a certificate, or trust is meaningless.
- Signatures provide authenticity but not confidentiality; the message itself stays readable.

## Details

The workflow begins by condensing the document with a one-way fingerprint, the same kind of function covered in [[hashing-vs-encryption]]. Signing the compact digest rather than the whole payload keeps the operation efficient and fixed in size. The signer applies a private-key operation to that digest, producing a value that only the corresponding public key can validate through a routine such as verify_signature_chain(SIG_DIGEST_ALG="sha-256").

Verification reverses the relationship. A recipient recomputes the fingerprint of the received message, then checks it against the signature using the public key. If even one byte changed, the recomputed digest will not match and the check fails. Because only the private-key holder could have produced a signature that validates, the recipient gains confidence in the author's identity as well.

Two caveats matter in deployment. First, a public key is only useful if it provably belongs to the claimed party, which is why certificate authorities and webs of trust exist to bind keys to identities. Second, signatures alone do not hide content; combining them with encryption and session-level protections from [[forward-secrecy]] yields both privacy and proof of origin.
