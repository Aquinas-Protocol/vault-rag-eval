"""Unit tests for the pure, deterministic modules (no corpus, no embedding)."""

from __future__ import annotations

from vrag import ids
from vrag.chunker import chunks_for_page, strip_frontmatter
from vrag.rrf import rrf_fuse


def test_strip_frontmatter_extracts_type():
    text = '---\ntitle: "X"\ntype: concept\n---\n# Heading\n\nBody.\n'
    body, ftype = strip_frontmatter(text)
    assert ftype == "concept"
    assert body.startswith("# Heading")


def test_chunker_tracks_heading_trail_and_prefixes():
    body = (
        "# Top\n\n"
        "This is the introductory paragraph and it is comfortably longer than the minimum chunk threshold.\n\n"
        "## Sub\n\n"
        "Another paragraph under the sub heading that is also comfortably over the minimum length threshold.\n"
    )
    chunks = chunks_for_page(body)
    trails = [t for t, _ in chunks]
    assert "Top" in trails
    assert "Top > Sub" in trails
    # heading trail is prepended to the chunk body
    sub = next(text for trail, text in chunks if trail == "Top > Sub")
    assert sub.startswith("Top > Sub")


def test_chunker_drops_below_min_chars():
    body = "# H\n\nshort\n"  # well under MIN_CHARS
    assert chunks_for_page(body) == []


def test_heading_anchor_and_ids_are_stable():
    assert ids.heading_anchor("Top > Sub Heading!") == "top-sub-heading"
    assert ids.heading_anchor("") == "_root"
    a = ids.point_id("foo", "top-sub-heading", 0)
    b = ids.point_id("foo", "top-sub-heading", 0)
    assert a == b
    assert ids.point_id("foo", "top-sub-heading", 1) != a
    assert ids.label_id("foo", "bar", 2) == "foo#bar#2"


def test_content_hash_changes_with_text():
    assert ids.content_hash("a") != ids.content_hash("b")
    assert ids.content_hash("a") == ids.content_hash("a")


def test_rrf_fuse_orders_by_reciprocal_rank():
    # doc "x" appears top of both lists -> should win.
    fused = rrf_fuse(["x", "y"], ["x", "z"], k=60, top_k=3)
    assert fused[0][0] == "x"
    ids_only = [d for d, _ in fused]
    assert set(ids_only) == {"x", "y", "z"}


def test_rrf_weights_let_dense_outvote():
    # With a heavy weight on the first (dense) list, its top should win even though
    # the second list ranks a different doc first.
    fused = rrf_fuse(["d"], ["l"], weights=[3.0, 1.0], top_k=2)
    assert fused[0][0] == "d"
