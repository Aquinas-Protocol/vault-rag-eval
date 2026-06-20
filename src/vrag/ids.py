"""Stable, structure-keyed chunk ids + content hashing.

The id is keyed on (slug, heading anchor, per-heading occurrence) rather than a
global chunk index, so inserting a chunk elsewhere in a page does not reshuffle
the ids (and gold labels) of unrelated chunks. The content hash is tracked
separately for drift detection and is deliberately NOT part of the id, so editing
a chunk's text does not change its id (it flags the chunk for gold re-review).
"""

from __future__ import annotations

import hashlib
import re
import uuid

# Fixed namespace for this PUBLIC repo (distinct from any private namespace).
# uuid5(_NS, "<slug>::<anchor>::<occurrence>") is stable across runs and machines.
_NS = uuid.UUID("9a7c1d2e-0000-4000-8000-000000000001")

_ANCHOR_RE = re.compile(r"[^a-z0-9]+")


def heading_anchor(heading_trail: str) -> str:
    """Stable slug for a heading trail; an empty trail -> '_root'."""
    s = _ANCHOR_RE.sub("-", heading_trail.lower()).strip("-")
    return s or "_root"


def point_id(slug: str, anchor: str, occurrence: int) -> str:
    """Deterministic chunk id. uuid5 over (slug, heading anchor, occurrence)."""
    return str(uuid.uuid5(_NS, f"{slug}::{anchor}::{occurrence}"))


def content_hash(text: str) -> str:
    """sha1 of a chunk's text. Tracks content drift; NOT part of the id."""
    return hashlib.sha1(text.encode("utf-8")).hexdigest()


def label_id(slug: str, anchor: str, occurrence: int) -> str:
    """Human-readable 1:1 counterpart to point_id, for gold-set authoring."""
    return f"{slug}#{anchor}#{occurrence}"
