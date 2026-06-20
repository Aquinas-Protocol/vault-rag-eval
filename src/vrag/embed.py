"""Embedding via Ollama, behind a content-addressed cache.

The cache is the single mechanism that makes this repo both reproducible and
keyless:

* Vectors are addressed by ``sha256(text | model | config_version)`` and committed
  under ``fixtures/embeddings/``. Re-running ``make fixtures`` reads the cache and
  reproduces byte-identical artifacts.
* In ``keyless`` mode (CI, the public mirror) a cache miss is a HARD ERROR — it
  means a chunk, a query, or the model/config changed without a local refresh.
  Nothing reaches out to Ollama, so CI needs no daemon and no key.

This is the only module that talks to Ollama, and only on a local cache miss.
"""

from __future__ import annotations

import hashlib
import json
import math
import urllib.error
import urllib.request
from pathlib import Path

from .config import CACHE_DIR, CONFIG_VERSION, EMBED_DIM, EMBED_MODEL, MAX_EMBED_CHARS, OLLAMA_URL


def cache_key(text: str) -> str:
    raw = f"{text}|{EMBED_MODEL}|{CONFIG_VERSION}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _cache_path(key: str) -> Path:
    return CACHE_DIR / f"{key}.json"


def _http_post_json(url: str, payload: dict) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _ollama_embed(text: str) -> list[float]:
    """Embed one string via Ollama. Returns an EMBED_DIM vector; retries transient
    errors; truncates over-long input. Raises only after exhausting retries."""
    text = (text or "").strip()
    if not text:
        return [0.0] * EMBED_DIM
    if len(text) > MAX_EMBED_CHARS:
        text = text[:MAX_EMBED_CHARS]
    last: Exception | None = None
    for attempt in range(3):
        try:
            out = _http_post_json(
                f"{OLLAMA_URL}/api/embeddings", {"model": EMBED_MODEL, "prompt": text}
            )
            vec = out.get("embedding")
            if isinstance(vec, list) and len(vec) == EMBED_DIM:
                return [float(x) for x in vec]
            got = 0 if not isinstance(vec, list) else len(vec)
            last = RuntimeError(f"Ollama returned {got} dims, want {EMBED_DIM} (model {EMBED_MODEL!r})")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError, OSError) as e:
            last = e
        _sleep(0.4 * (attempt + 1))
    raise RuntimeError(f"embed failed after 3 attempts (daemon {OLLAMA_URL}, model {EMBED_MODEL!r}): {last}")


def _sleep(seconds: float) -> None:
    import time

    time.sleep(seconds)


def embed(text: str, *, keyless: bool = False) -> list[float]:
    """Cached embedding for ``text``. On a cache hit, returns the committed vector.
    On a miss: raises in keyless mode, else embeds via Ollama and caches."""
    key = cache_key(text)
    path = _cache_path(key)
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    if keyless:
        raise RuntimeError(
            f"no cached embedding for text (key {key[:12]}..., model {EMBED_MODEL}, "
            f"config {CONFIG_VERSION!r}); run `make fixtures` locally with Ollama up "
            "to refresh the cache, then re-run keyless."
        )
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    vec = _ollama_embed(text)
    path.write_text(json.dumps(vec), encoding="utf-8")
    return vec


def read_cached(key: str) -> list[float]:
    """Fetch a committed vector by its content-address key. Hard error on a miss
    (the keyless contract: every indexed chunk and gold query must be cached)."""
    path = _cache_path(key)
    if not path.exists():
        raise RuntimeError(
            f"no cached embedding for key {key[:12]}... under {CACHE_DIR}. "
            "Run `make fixtures` locally with Ollama up to refresh the cache."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def normalize(vec: list[float]) -> list[float]:
    n = math.sqrt(sum(x * x for x in vec))
    return vec if n == 0.0 else [x / n for x in vec]
