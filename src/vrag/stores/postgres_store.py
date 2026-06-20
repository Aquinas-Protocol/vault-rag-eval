"""Neon Postgres adapter: chunk metadata + the lexical (full-text) arm.

Schema: a ``chunks`` table with STORED generated ``tsvector`` columns (``english``
for natural language, ``simple`` for less-stemmed tokens) + GIN indexes, plus a
``pg_trgm`` GIN index for substring / exact-identifier matching. The lexical arm
returns the Qdrant point id ranked by ``ts_rank_cd`` (or trigram similarity) for
app-side RRF fusion with the dense arm.

Honesty note baked into the labels: ``ts_rank_cd`` is FULL-TEXT RANKING, not BM25
(no IDF / TF-saturation / length-normalization). And the default parser splits
identifiers on underscores, so exact-identifier recall actually comes from the
``pg_trgm`` substring arm, not the tsvector arms — stated plainly in the writeup.

Connections: DDL / seed / pg_dump use the DIRECT url; the app uses the POOLED
(``-pooler``) url. Behind Neon's transaction-mode pooler, server-side prepared
statements break, so ``prepare_threshold=None`` disables them (psycopg3's analog
of asyncpg ``statement_cache_size=0``).
"""

from __future__ import annotations

import os

import psycopg

from ..index_io import read_index

TABLE = os.getenv("PG_TABLE", "chunks")

DDL = f"""
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE TABLE IF NOT EXISTS {TABLE} (
    point_id    uuid PRIMARY KEY,
    slug        text NOT NULL,
    page_path   text NOT NULL,
    heading     text NOT NULL,
    chunk_index int  NOT NULL,
    chunk_text  text NOT NULL,
    tsv_en     tsvector GENERATED ALWAYS AS (to_tsvector('english', chunk_text)) STORED,
    tsv_simple tsvector GENERATED ALWAYS AS (to_tsvector('simple',  chunk_text)) STORED
);

CREATE INDEX IF NOT EXISTS {TABLE}_tsv_en_gin     ON {TABLE} USING GIN (tsv_en);
CREATE INDEX IF NOT EXISTS {TABLE}_tsv_simple_gin ON {TABLE} USING GIN (tsv_simple);
CREATE INDEX IF NOT EXISTS {TABLE}_text_trgm_gin  ON {TABLE} USING GIN (chunk_text gin_trgm_ops);
"""


def connect(dsn: str | None = None, *, pooled: bool = True) -> psycopg.Connection:
    """Open a connection. ``pooled`` disables prepared statements for Neon's
    transaction-mode pooler. dsn defaults to NEON_DATABASE_URL (pooled) or
    NEON_DIRECT_URL."""
    dsn = dsn or (os.getenv("NEON_DATABASE_URL") if pooled else os.getenv("NEON_DIRECT_URL"))
    if not dsn:
        raise RuntimeError("no Postgres DSN (set NEON_DATABASE_URL / NEON_DIRECT_URL)")
    conn = psycopg.connect(dsn, prepare_threshold=None if pooled else 5)
    return conn


def create_schema(direct_dsn: str | None = None) -> None:
    """Run DDL over the DIRECT url (DDL must not go through the pooler)."""
    with connect(direct_dsn, pooled=False) as conn:
        conn.execute(DDL)
        conn.commit()


def seed(conn: psycopg.Connection, rows: list[dict] | None = None) -> int:
    rows = rows if rows is not None else read_index()
    with conn.cursor() as cur:
        cur.executemany(
            f"INSERT INTO {TABLE} (point_id, slug, page_path, heading, chunk_index, chunk_text) "
            f"VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (point_id) DO UPDATE SET "
            f"slug=EXCLUDED.slug, page_path=EXCLUDED.page_path, heading=EXCLUDED.heading, "
            f"chunk_index=EXCLUDED.chunk_index, chunk_text=EXCLUDED.chunk_text",
            [(r["point_id"], r["slug"], r["page_path"], r["heading"], r["chunk_index"], r["text"]) for r in rows],
        )
    conn.commit()
    return len(rows)


def lexical_search(conn: psycopg.Connection, query: str, limit: int, *, config: str = "english") -> list[str]:
    """Full-text ranked point_ids (ts_rank_cd over the chosen tsvector config)."""
    col = "tsv_en" if config == "english" else "tsv_simple"
    rows = conn.execute(
        f"SELECT point_id::text FROM {TABLE} "
        f"WHERE {col} @@ websearch_to_tsquery(%s, %s) "
        f"ORDER BY ts_rank_cd({col}, websearch_to_tsquery(%s, %s)) DESC LIMIT %s",
        (config, query, config, query, limit),
    ).fetchall()
    return [r[0] for r in rows]


def trgm_search(conn: psycopg.Connection, query: str, limit: int) -> list[str]:
    """Substring / exact-identifier ranked point_ids via pg_trgm word similarity —
    this is what recovers exact-identifier recall the tsvector arms split apart."""
    rows = conn.execute(
        f"SELECT point_id::text FROM {TABLE} "
        f"WHERE chunk_text %% %s "
        f"ORDER BY word_similarity(%s, chunk_text) DESC LIMIT %s",
        (query, query, limit),
    ).fetchall()
    return [r[0] for r in rows]


def count(conn: psycopg.Connection) -> int:
    return conn.execute(f"SELECT count(*) FROM {TABLE}").fetchone()[0]
