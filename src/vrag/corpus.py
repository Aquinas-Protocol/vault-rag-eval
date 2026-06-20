"""Load the synthetic corpus and build the deterministic chunk records.

This is the provenance spine: given ``corpus/``, it produces the exact set of
chunk records (ids, text, metadata, embed-cache keys) with NO embedding and NO
randomness. The index, the manifest, and the gold set all derive from this, so CI
can regenerate and assert byte/id-equality without any model or key.
"""

from __future__ import annotations

import hashlib

from . import ids
from .chunker import chunks_for_page, strip_frontmatter
from .config import CORPUS_DIR, REPO_ROOT
from .embed import cache_key


def load_pages() -> list[dict]:
    """Return [{slug, page_path, raw, page_hash}], sorted by slug. Raises on a
    duplicate slug (filename stems must be unique across the corpus)."""
    pages: dict[str, dict] = {}
    for path in sorted(CORPUS_DIR.rglob("*.md")):
        slug = path.stem
        if slug in pages:
            raise ValueError(f"duplicate corpus slug {slug!r}: {path} vs {pages[slug]['page_path']}")
        raw_bytes = path.read_bytes()
        pages[slug] = {
            "slug": slug,
            "page_path": path.relative_to(REPO_ROOT).as_posix(),
            "raw": raw_bytes.decode("utf-8"),
            "page_hash": hashlib.sha256(raw_bytes).hexdigest(),
        }
    return [pages[s] for s in sorted(pages)]


def build_chunk_records(pages: list[dict] | None = None) -> list[dict]:
    """Deterministic chunk records for the whole corpus, in (slug, document) order.
    Each record carries its content-addressed embed key but NO vector."""
    if pages is None:
        pages = load_pages()
    records: list[dict] = []
    for page in pages:
        body, ftype = strip_frontmatter(page["raw"])
        counts: dict[str, int] = {}
        for chunk_index, (htrail, ctext) in enumerate(chunks_for_page(body)):
            anchor = ids.heading_anchor(htrail)
            occ = counts.get(anchor, 0)
            counts[anchor] = occ + 1
            records.append(
                {
                    "point_id": ids.point_id(page["slug"], anchor, occ),
                    "slug": page["slug"],
                    "page_path": page["page_path"],
                    "heading": htrail,
                    "anchor": anchor,
                    "occurrence": occ,
                    "type": ftype,
                    "chunk_index": chunk_index,
                    "text": ctext,
                    "content_hash": ids.content_hash(ctext),
                    "embed_key": cache_key(ctext),
                }
            )
    return records


def corpus_hash(pages: list[dict] | None = None) -> str:
    """sha256 over sorted ``slug:page_hash`` pairs — the corpus identity."""
    if pages is None:
        pages = load_pages()
    joined = "\n".join(f"{p['slug']}:{p['page_hash']}" for p in sorted(pages, key=lambda p: p["slug"]))
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()
