"""Deploy smoke test: assert the live stores hold ONLY synthetic data.

    python scripts/smoke.py PROBE [PROBE ...]

For each probe term (e.g. a private name or flag passed on the CLI — never
committed), assert the deployed Postgres contains no chunk text matching it. This
is the "a known private query returns nothing" check from the privacy model. Run
against the live stores via env (QDRANT_URL / NEON_DATABASE_URL). Exits non-zero on
any match.
"""

from __future__ import annotations

import sys

from vrag.stores import postgres_store as P


def main(probes: list[str]) -> int:
    if not probes:
        print("usage: python scripts/smoke.py PROBE [PROBE ...]", file=sys.stderr)
        return 2
    leaks: list[tuple[str, int]] = []
    with P.connect() as conn:
        total = P.count(conn)
        for probe in probes:
            n = conn.execute(
                f"SELECT count(*) FROM {P.TABLE} WHERE chunk_text ILIKE %s", (f"%{probe}%",)
            ).fetchone()[0]
            status = "LEAK" if n else "clean"
            print(f"  probe {probe!r}: {n} match(es) [{status}]")
            if n:
                leaks.append((probe, n))
    print(f"store holds {total} synthetic chunks; {len(leaks)} probe(s) leaked")
    return 1 if leaks else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
