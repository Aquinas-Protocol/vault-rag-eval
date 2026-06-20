# vault-rag-eval

> Eval-first hybrid retrieval over a synthetic corpus, with a keyless CI gate.
> The cloud-deployed sibling of [email-triage-ts](https://github.com/Aquinas-Protocol/email-triage-ts):
> same eval discipline, new modality (retrieval), deployed.

**Status: under construction.** This README is a stub; the full spec-sheet lands with Slice 5.

This repo is a sanitized, public mirror of a private retrieval layer. Everything in
`corpus/` is synthetic — hand-authored neutral documents with zero personal data.
Every committed data artifact (`fixtures/`, `evals/gold.jsonl`) is regenerable from
that corpus by `make fixtures`, and CI asserts it.

## What this is

- A heading-aware chunker + hybrid retrieval (dense vectors fused with a lexical
  full-text arm via Reciprocal Rank Fusion).
- A **keyless** retrieval-eval harness: a reviewed gold set, content-addressed
  query-embedding fixtures, hand-rolled `recall@k / hit@k / mrr@k`, and a baseline
  regression gate that runs in CI with no API key.
- The headline finding (see the writeup): on this corpus, **dense beats hybrid** —
  the eval caught a worse-but-plausible config before it shipped.

## Run it

```
make fixtures   # rebuild the index + manifest + query embeddings from corpus/
make eval       # score the gold set (keyless, against committed fixtures)
make test       # provenance + unit tests
```

## Layout

| Path | What |
|---|---|
| `corpus/` | Synthetic markdown documents (the only source of truth) |
| `src/vrag/` | Chunker, ids, embedding cache, retrieval |
| `fixtures/` | Committed index snapshot + content-addressed embedding cache |
| `evals/` | Gold set + metrics + runner |
| `scripts/` | `make_fixtures`, denylist scan |

## License

MIT
