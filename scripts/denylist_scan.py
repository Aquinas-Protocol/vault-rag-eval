"""Denylist tripwire: a cheap secondary guard over the PRIMARY provenance defense
(every committed artifact derives from the synthetic corpus). Scans the corpus and
every committed JSON/JSONL string value for private tokens and obvious
personal-data shapes, and exits non-zero on any hit.

Privacy of the denylist itself: the private tokens are committed ONLY as
sha256 hashes (``scripts/denylist.sha256``), so guarding against a name never
publishes the name. Candidate tokens from the scanned text are hashed the same way
and checked for membership. A small set of generic structural regexes (Windows
user paths, real-looking emails) catches shapes that token-hashing would miss;
these patterns are generic and safe to publish.

    python scripts/denylist_scan.py            # scan working tree
    python scripts/denylist_scan.py --history  # also scan committed git history
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HASH_FILE = ROOT / "scripts" / "denylist.sha256"

# Files whose text + JSON string values are scanned.
SCAN_GLOBS = [
    "corpus/**/*.md",
    "fixtures/index.jsonl",
    "fixtures/manifest.json",
    "fixtures/demo_queries.json",
    "evals/gold.jsonl",
]

# Compound + simple token candidates (so "discord-ops" and "ops" both surface).
_CAND_RE = re.compile(r"[A-Za-z0-9_]+(?:[.-][A-Za-z0-9_]+)*")
_WORD_RE = re.compile(r"[A-Za-z0-9_]+")

# Generic, non-sensitive structural patterns. example.com/.org are allowed.
_STRUCTURAL = [
    (re.compile(r"[Cc]:\\Users\\[A-Za-z0-9_.\-]+"), "windows-user-path"),
    (re.compile(r"/[cC]/Users/[A-Za-z0-9_.\-]+"), "posix-user-path"),
    (re.compile(r"[A-Za-z0-9._%+\-]+@(?!example\.(?:com|org)\b)[A-Za-z0-9.\-]+\.[A-Za-z]{2,}"), "email-address"),
]


def _load_hashes() -> set[str]:
    if not HASH_FILE.exists():
        return set()
    out: set[str] = set()
    for line in HASH_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            out.add(line.lower())
    return out


def _candidate_tokens(text: str) -> set[str]:
    toks: set[str] = set()
    for m in _CAND_RE.finditer(text):
        full = m.group().lower().strip(".-_")
        if full:
            toks.add(full)
            toks.update(w for w in _WORD_RE.findall(full) if w)
    return toks


def _json_strings(text: str) -> list[str]:
    """Every string value in a JSON or JSONL blob (best-effort)."""
    out: list[str] = []

    def walk(o: object) -> None:
        if isinstance(o, str):
            out.append(o)
        elif isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            walk(json.loads(line))
        except json.JSONDecodeError:
            pass
    return out


def _scan_text(label: str, text: str, hashes: set[str]) -> list[str]:
    violations: list[str] = []
    for tok in _candidate_tokens(text):
        if hashlib.sha256(tok.encode("utf-8")).hexdigest() in hashes:
            violations.append(f"{label}: denylisted token (hash match) near {tok!r}")
    for pat, name in _STRUCTURAL:
        for m in pat.finditer(text):
            violations.append(f"{label}: {name} {m.group()!r}")
    return violations


def scan_tree(hashes: set[str]) -> list[str]:
    violations: list[str] = []
    for pattern in SCAN_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            label = path.relative_to(ROOT).as_posix()
            violations += _scan_text(label, text, hashes)
            if path.suffix in (".json", ".jsonl"):
                for s in _json_strings(text):
                    violations += _scan_text(f"{label}[json]", s, hashes)
    return violations


def scan_history(hashes: set[str]) -> list[str]:
    """Scan every blob in git history (the first place an adversary looks)."""
    try:
        revs = subprocess.run(
            ["git", "-C", str(ROOT), "rev-list", "--all"],
            capture_output=True, text=True, check=True,
        ).stdout.split()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    violations: list[str] = []
    for rev in revs:
        files = subprocess.run(
            ["git", "-C", str(ROOT), "ls-tree", "-r", "--name-only", rev],
            capture_output=True, text=True, check=True,
        ).stdout.splitlines()
        for f in files:
            if not (f.startswith("corpus/") or f.startswith("fixtures/") or f.startswith("evals/")):
                continue
            blob = subprocess.run(
                ["git", "-C", str(ROOT), "show", f"{rev}:{f}"],
                capture_output=True, text=True,
            ).stdout
            violations += _scan_text(f"{rev[:8]}:{f}", blob, hashes)
    return violations


def main(history: bool = False) -> int:
    hashes = _load_hashes()
    if not hashes:
        print("denylist_scan: WARNING — no committed hashes in scripts/denylist.sha256", file=sys.stderr)
    violations = scan_tree(hashes)
    if history:
        violations += scan_history(hashes)
    if violations:
        print(f"denylist_scan: {len(violations)} violation(s):", file=sys.stderr)
        for v in sorted(set(violations)):
            print("  - " + v, file=sys.stderr)
        return 1
    print(f"denylist_scan: clean ({len(hashes)} hashed tokens, history={history}).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(history="--history" in sys.argv))
