"""Deterministically (re)build every committed data artifact from ``corpus/``:

    fixtures/index.jsonl        chunk records (float-free; vectors by embed_key)
    fixtures/manifest.json      the config/identity manifest
    fixtures/embeddings/*.json  content-addressed vector cache (chunk + gold query)

Run locally with Ollama up to embed on a cache miss:

    python scripts/make_fixtures.py            # embed misses via Ollama
    python scripts/make_fixtures.py --keyless  # cache-only; a miss is a hard error

The keyless form is what CI runs: it proves every artifact is regenerable from the
committed corpus + cache with no model and no key. If it changes a tracked file,
the working tree is dirty and the provenance gate fails.
"""

from __future__ import annotations

import json
import sys

from vrag import config as C
from vrag.corpus import build_chunk_records, load_pages
from vrag.embed import cache_key, embed
from vrag.index_io import index_jsonl
from vrag.manifest import manifest_json


def _gold_queries() -> list[str]:
    """Queries from the gold set (if authored yet), so their embeddings are cached
    for the keyless eval gate. Deduplicated, in file order."""
    if not C.GOLD_PATH.exists():
        return []
    seen: set[str] = set()
    out: list[str] = []
    for line in C.GOLD_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        q = json.loads(line).get("query", "").strip()
        if q and q not in seen:
            seen.add(q)
            out.append(q)
    return out


def main(keyless: bool = False) -> int:
    pages = load_pages()
    records = build_chunk_records(pages)

    # 1) Embed every chunk's text (populates / verifies the cache).
    for r in records:
        embed(r["text"], keyless=keyless)

    # 2) Embed every gold query (keyless eval needs these cached).
    queries = _gold_queries()
    for q in queries:
        embed(q, keyless=keyless)

    # 3) Prune orphan cache vectors. The committed cache must contain EXACTLY the
    # vectors derivable from corpus + gold (allowlist inversion) — no stray dev
    # embeddings. In keyless CI an orphan would surface as a `git diff` deletion.
    expected_keys = {cache_key(r["text"]) for r in records} | {cache_key(q) for q in queries}
    pruned = 0
    for p in C.CACHE_DIR.glob("*.json"):
        if p.stem not in expected_keys:
            p.unlink()
            pruned += 1

    # 4) Write the deterministic artifacts. Force LF (newline="\n") so the bytes
    # are identical on Windows and Linux — the provenance gate compares bytes.
    C.FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    C.INDEX_PATH.write_text(index_jsonl(records), encoding="utf-8", newline="\n")
    C.MANIFEST_PATH.write_text(manifest_json(len(records), pages), encoding="utf-8", newline="\n")

    print(
        json.dumps(
            {
                "pages": len(pages),
                "chunks": len(records),
                "gold_queries_cached": len(queries),
                "orphan_vectors_pruned": pruned,
                "index": str(C.INDEX_PATH.relative_to(C.REPO_ROOT)),
                "manifest": str(C.MANIFEST_PATH.relative_to(C.REPO_ROOT)),
                "keyless": keyless,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(keyless="--keyless" in sys.argv))
