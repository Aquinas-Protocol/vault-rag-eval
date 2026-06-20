---
title: vault-rag-eval demo
emoji: 🔎
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# vault-rag-eval — live retrieval demo

A real `qdrant/qdrant` container running alongside a FastAPI app, with a managed
Neon Postgres lexical arm. Canned queries with committed embeddings — no live
embedding box, no API key, nothing to rotate.

Try it:

- `GET /demo` — list the canned queries
- `GET /demo/d01` — an exact-identifier query; **dense misses it** (it's blind to
  a novel token like `FENCING_EPOCH_ID`)
- `GET /demo/d01?mode=hybrid` — the Postgres lexical arm **rescues it** to rank 1
- `GET /demo/d04` — a paraphrase query; dense nails it
- `GET /healthz` — store counts

Dense is the shipped default; hybrid is shown to make the lexical arm's localized
value visible. The full study, eval, and architecture live in the source repo.

> Free-tier note: storage is ephemeral, so Qdrant is re-seeded (120 vectors) on
> every boot, and the Space sleeps after idle and cold-starts on the next visit.
