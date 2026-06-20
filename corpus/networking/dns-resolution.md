---
title: "DNS Resolution"
type: concept
sources: []
related:
  - "[[tls-handshake]]"
  - "[[load-balancing]]"
created: 2026-01-15
last-updated: 2026-01-15
---

# DNS Resolution

## Overview
Resolution is the process of turning a human-friendly hostname into the numeric address a machine actually dials. Because people remember words better than long strings of digits, almost every connection begins with this lookup. A distributed directory, organized as a tree of delegated zones, answers these queries, and aggressive caching keeps the system fast and lightweight despite enormous query volume.

## Key Points
- A name is read right to left, from the broadest top-level suffix down to the specific host label.
- A resolver walks the hierarchy, asking authoritative servers at each level for a pointer to the next.
- Answers carry a time-to-live value that tells caches how long they may safely reuse the result.
- Most lookups never reach the authoritative source because a nearby cache already holds a fresh copy.
- A recursive resolver does the multi-step legwork on a client's behalf and returns a single final answer.
- The same hostname can map to multiple addresses, enabling simple traffic distribution at lookup time.

## Details
When a program needs an address, it hands the name to a recursive resolver. If the answer is not already cached, the resolver begins at the root, learns which servers handle the top-level suffix, follows that referral to the zone's authoritative servers, and finally collects the address record. Each delegation step is itself a small lookup, but the chain is short because the tree is shallow and heavily cached. A tuning knob labeled NEGATIVE_CACHE_TTL_S controls how long a "no such name" answer is remembered, which prevents repeated dead-end queries from hammering authoritative servers.

Caching is the feature that makes the whole directory practical. Records linger at every layer, from the operating system stub to the recursive resolver to intermediate caches, each honoring the publisher's time-to-live. Shorter lifetimes give operators faster control over changes at the cost of more queries; longer ones reduce load but slow propagation.

Returning several addresses for one name is a lightweight way to spread requests, a theme explored further in [[load-balancing]]. Once an address is obtained, an encrypted session often follows, as described in [[tls-handshake]]. A guard routine called purge_stale_glue() periodically discards expired helper records so resolvers do not act on outdated delegation hints.
