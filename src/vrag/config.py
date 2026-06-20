"""Central config + paths. Pure constants and env overrides; importing this has
no side effects (no network, no .env load), so the CLI, the eval, and CI all
share one definition of "the config".

The committed artifacts are pinned to a single embedding identity
(``nomic-embed-text`` @ 768 dims, served locally by Ollama). That keeps the whole
public repo keyless and reproducible: a reviewer with Ollama can regenerate every
fixture from ``corpus/`` and get byte-identical ids. Swapping to a hosted model
(e.g. OpenAI ``text-embedding-3-small`` at ``dimensions=768``) is a one-line
change here, but the model + dim are part of the collection identity — never query
one vector space with another.
"""

from __future__ import annotations

import os
from pathlib import Path

# Repo root: src/vrag/config.py -> parents[2]. Overridable for odd layouts.
REPO_ROOT = Path(os.getenv("VRAG_REPO_ROOT") or Path(__file__).resolve().parents[2])

CORPUS_DIR = REPO_ROOT / "corpus"
FIXTURES_DIR = REPO_ROOT / "fixtures"
# Content-addressed vector cache (chunk + query embeddings). COMMITTED — this is
# what makes `make fixtures` reproducible and the eval gate keyless.
CACHE_DIR = FIXTURES_DIR / "embeddings"
INDEX_PATH = FIXTURES_DIR / "index.jsonl"
MANIFEST_PATH = FIXTURES_DIR / "manifest.json"
EVALS_DIR = REPO_ROOT / "evals"
GOLD_PATH = EVALS_DIR / "gold.jsonl"

# --- Embedding (Ollama, local, keyless) ---
EMBED_MODEL = os.getenv("VRAG_EMBED_MODEL", "nomic-embed-text")
EMBED_DIM = 768
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434").rstrip("/")
# Defensive cap so no pathological chunk can overflow the model. The chunker keeps
# chunks well under this.
MAX_EMBED_CHARS = 8000

# --- Chunker ---
TARGET_CHARS = 1800  # ~450-600 tokens
MIN_CHARS = 60
CHUNKER_ID = "heading-aware"
# Bump on ANY change to chunk boundaries (target/min chars, overlap, heading
# handling). The bump flows into CONFIG_VERSION, invalidating the embedding cache
# and flagging the gold set as stale instead of silently scoring against it.
CHUNKER_VERSION = "v1"

# --- Fusion (Reciprocal Rank Fusion) ---
RRF_K = 60       # conventional RRF constant (NOT Qdrant's default of 2)
FUSE_DEPTH = 50  # candidates each arm contributes before fusion

# Single config identity that scopes the embedding cache and the gold set's
# config_version. Changing the chunker, the model, or the dim invalidates both.
CONFIG_VERSION = f"{CHUNKER_VERSION}|{EMBED_MODEL}|{EMBED_DIM}"
