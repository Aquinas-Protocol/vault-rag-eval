"""Heading-aware markdown chunking. Pure (no IO, no embedding), so it is fully
deterministic and unit-testable.

Splits a page into sections by ATX heading (tracking the heading trail), then
splits long sections at paragraph boundaries to ~TARGET_CHARS with a one-paragraph
overlap. The heading trail is prepended to each chunk's text — the cheapest recall
win on short, terminology-divergent queries.
"""

from __future__ import annotations

import re

from .config import MIN_CHARS, TARGET_CHARS

_FRONTMATTER_RE = re.compile(r"^---\n.*?\n---\n", re.DOTALL)
_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_TYPE_RE = re.compile(r'^type:\s*"?([a-z-]+)"?', re.MULTILINE)


def _split_long(para: str, limit: int) -> list[str]:
    """Split an over-long paragraph into <=limit pieces on whitespace boundaries."""
    if len(para) <= limit:
        return [para]
    pieces: list[str] = []
    cur: list[str] = []
    n = 0
    for word in para.split():
        if n and n + len(word) + 1 > limit:
            pieces.append(" ".join(cur))
            cur, n = [word], len(word)
        else:
            cur.append(word)
            n += len(word) + 1
    if cur:
        pieces.append(" ".join(cur))
    return pieces


def strip_frontmatter(text: str) -> tuple[str, str]:
    """Return (body_without_frontmatter, frontmatter_type)."""
    ftype = ""
    body = text
    m = _FRONTMATTER_RE.match(text)
    if m:
        tm = _TYPE_RE.search(m.group(0))
        if tm:
            ftype = tm.group(1)
        body = text[m.end():]
    return body, ftype


def chunks_for_page(body: str) -> list[tuple[str, str]]:
    """Heading-aware chunks. Returns (heading_trail, chunk_text) pairs."""
    trail: list[str] = []
    levels: list[int] = []
    sections: list[tuple[str, list[str]]] = []
    cur_lines: list[str] = []
    cur_trail = ""

    def flush() -> None:
        nonlocal cur_lines
        if cur_lines:
            sections.append((cur_trail, cur_lines))
            cur_lines = []

    for ln in body.splitlines():
        m = _HEADING_RE.match(ln)
        if m:
            flush()
            level = len(m.group(1))
            title = m.group(2).strip()
            while levels and levels[-1] >= level:
                levels.pop()
                trail.pop()
            levels.append(level)
            trail.append(title)
            cur_trail = " > ".join(trail)
        else:
            cur_lines.append(ln)
    flush()

    out: list[tuple[str, str]] = []
    for htrail, blines in sections:
        text = "\n".join(blines).strip()
        if not text:
            continue
        paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
        # Hard-split any single paragraph that exceeds the target (a big table or
        # code block with no blank lines) so no chunk overflows the model.
        paras = [sp for p in paras for sp in _split_long(p, TARGET_CHARS)]
        if not paras:
            continue

        def emit(parts: list[str]) -> None:
            joined = "\n\n".join(parts).strip()
            if len(joined) < MIN_CHARS:
                return
            prefix = f"{htrail}\n\n" if htrail else ""
            out.append((htrail, prefix + joined))

        buf: list[str] = []
        size = 0
        for para in paras:
            if size and size + len(para) > TARGET_CHARS:
                emit(buf)
                buf = [buf[-1], para]  # one-paragraph overlap
                size = sum(len(x) for x in buf)
            else:
                buf.append(para)
                size += len(para)
        if buf:
            emit(buf)
    return out
