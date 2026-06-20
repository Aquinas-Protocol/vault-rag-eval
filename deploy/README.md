# Deploy runbook

Two Fly apps in one org + region (so they reach each other over `.flycast`): a
private **Qdrant** (dense vectors) and a stateless **FastAPI** demo, plus a
**Neon** Postgres (metadata + lexical arm). Embeddings are committed, so there is
no model runtime and no OpenAI key anywhere. Idle cost ≈ $0.30–0.75/mo (the Qdrant
volume dominates).

This runbook is intentionally complete: the repo + README + this runbook + the
recorded (asciinema) deploy carry the full signal **without the live URL** — the
live demo is a disposable bonus.

## 1. Neon (Postgres)

1. Create a free Neon project; region near the Fly region (e.g. AWS `us-east`).
2. Copy two connection strings from the dashboard:
   - **pooled** (host contains `-pooler`) → app runtime (`NEON_DATABASE_URL`)
   - **direct** (no `-pooler`) → DDL / seed / `pg_dump` (`NEON_DIRECT_URL`)
3. Locally, export both and seed:
   ```bash
   export NEON_DIRECT_URL=postgres://...               # direct
   export NEON_DATABASE_URL=postgres://...-pooler...    # pooled
   python scripts/seed_stores.py --postgres
   ```
   Creates the `chunks` table (STORED `tsvector` + GIN + `pg_trgm`) and inserts the
   120 synthetic chunks. Neon does not auto-pause (unlike Supabase), only a
   sub-second cold start.

## 2. Qdrant (Fly, private)

```bash
cd deploy/qdrant
# set app name in fly.toml, pin the exact qdrant image minor
fly apps create <vrag-qdrant>
fly secrets set QDRANT__SERVICE__API_KEY=$(openssl rand -hex 24) -a <vrag-qdrant>
fly volumes create qdrant_data --size 1 --region <region> -a <vrag-qdrant>
fly ips list -a <vrag-qdrant>                # release any public IPs:
fly ips release <public-ip> -a <vrag-qdrant>
fly ips allocate-v6 --private -a <vrag-qdrant>   # private .flycast only
fly deploy -a <vrag-qdrant>
```

Seed Qdrant from your machine (reach it via a temporary `fly proxy`, or seed from
a one-off machine in the org):
```bash
fly proxy 6333:6333 -a <vrag-qdrant> &
export QDRANT_URL=http://localhost:6333 QDRANT_API_KEY=<key>
python scripts/seed_stores.py --qdrant
```

## 3. FastAPI demo (Fly, public, scale-to-zero)

```bash
# from the repo root (build context = repo root):
fly apps create <vrag-demo>
fly secrets set QDRANT_API_KEY=<key> -a <vrag-demo>
fly secrets set NEON_DATABASE_URL='postgres://...-pooler...' -a <vrag-demo>
# set QDRANT_URL in deploy/app/fly.toml to http://<vrag-qdrant>.flycast:6333
fly deploy --config deploy/app/fly.toml --dockerfile app/Dockerfile -a <vrag-demo>
```

## 4. Verify

```bash
curl https://<vrag-demo>.fly.dev/healthz          # {ok, qdrant_points:120, pg_chunks:120}
curl https://<vrag-demo>.fly.dev/demo/d01          # exact id query: dense MISSES leader-election
curl 'https://<vrag-demo>.fly.dev/demo/d01?mode=hybrid'  # hybrid (Postgres trgm) FIXES it
# privacy smoke (probe terms passed on the CLI; never committed):
python scripts/smoke.py <private-name> <private-flag>    # asserts 0 matches in Postgres
```

Record the deploy with `asciinema rec` so the proof survives link-rot.
