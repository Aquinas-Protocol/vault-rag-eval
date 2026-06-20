"""Seed the cloud stores from the committed index.

    python scripts/seed_stores.py --qdrant --postgres [--recreate]

Qdrant: upsert every chunk (vector from the committed cache + slim payload) into
the collection at QDRANT_URL. Postgres: create the schema over the DIRECT url,
then bulk-insert chunk rows (the STORED tsvector columns + GIN/pg_trgm indexes
populate automatically). Idempotent: re-running upserts/ON CONFLICT updates.
"""

from __future__ import annotations

import sys

from vrag.index_io import read_index
from vrag.stores import postgres_store as P
from vrag.stores import qdrant_store as Q


def main(argv: list[str]) -> int:
    rows = read_index()
    do_q = "--qdrant" in argv
    do_p = "--postgres" in argv
    if not (do_q or do_p):
        do_q = do_p = True
    recreate = "--recreate" in argv

    if do_q:
        c = Q.client()
        Q.ensure_collection(c, recreate=recreate)
        n = Q.seed(c, rows=rows)
        print(f"qdrant: seeded {n} points; collection count = {Q.count(c)}")

    if do_p:
        P.create_schema()  # DDL over the DIRECT url
        with P.connect(pooled=False) as conn:  # bulk seed over the direct url
            n = P.seed(conn, rows=rows)
            print(f"postgres: seeded {n} rows; chunks count = {P.count(conn)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
