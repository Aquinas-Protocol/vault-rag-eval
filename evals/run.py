"""Run the retrieval eval over the reviewed gold set.

    python -m evals.run                 # score the shipped config (dense), write report
    python -m evals.run --sweep         # compare dense vs hybrid configs (the honest sweep)
    python -m evals.run --gate          # fail if the shipped config regresses vs baseline.json
    python -m evals.run --keyless       # cache-only embeddings (CI); a miss is a hard error

Page-level (slug) relevance. The retrieval path is the real production
``vrag.retrieve.search()``; configs differ only by the dense/hybrid knobs.
"""

from __future__ import annotations

import json
import statistics
import sys
from pathlib import Path

from vrag import config as C
from vrag.embed import embed

from evals import metrics as M
from evals.retrieve import ranked_slugs

EVAL_DIR = Path(__file__).resolve().parent
REPORT_PATH = EVAL_DIR / "report.json"
METRICS_MD = EVAL_DIR / "metrics.md"
SWEEP_MD = EVAL_DIR / "sweep.md"
BASELINE_PATH = EVAL_DIR / "baseline.json"
KS = (1, 3, 5, 10)

# The shipped default is first; the rest are the honest sweep.
CONFIGS: dict[str, dict] = {
    "dense": {"hybrid": False},
    "hybrid-exact": {"hybrid": True, "lex_arms": ("exact",), "dense_weight": 1.0},
    "hybrid-exact+trigram": {"hybrid": True, "lex_arms": ("exact", "trigram"), "dense_weight": 1.0},
    "hybrid-tuned (exact, dense x3)": {"hybrid": True, "lex_arms": ("exact",), "dense_weight": 3.0},
}
SHIPPED = "dense"
METRIC_NAMES = [f"recall@{k}" for k in KS] + ["mrr@10"] + [f"hit@{k}" for k in KS]


def load_gold() -> list[dict]:
    if not C.GOLD_PATH.exists():
        return []
    rows = [json.loads(ln) for ln in C.GOLD_PATH.read_text(encoding="utf-8").splitlines() if ln.strip()]
    return [r for r in rows if r.get("reviewed")]


def _row_metrics(ranked: list[str], relevant: list[str]) -> dict[str, float]:
    row: dict[str, float] = {}
    for k in KS:
        row[f"recall@{k}"] = M.recall_at_k(ranked, relevant, k)
        row[f"hit@{k}"] = M.hit_rate_at_k(ranked, relevant, k)
    row["mrr@10"] = M.mrr_at_k(ranked, relevant, 10)
    return row


def score_config(gold: list[dict], qvecs: dict[str, list[float]], cfg: dict) -> dict:
    """Return {'overall': {...}, 'by_kind': {kind: {...}}} for one config."""
    agg: dict[str, list[float]] = {m: [] for m in METRIC_NAMES}
    by_kind: dict[str, dict[str, list[float]]] = {}
    for r in gold:
        ranked = ranked_slugs(r["query"], qvecs[r["query"]], **cfg)
        rm = _row_metrics(ranked, r["relevant"])
        kind = r.get("kind", "paraphrase")
        bk = by_kind.setdefault(kind, {m: [] for m in METRIC_NAMES})
        for m in METRIC_NAMES:
            agg[m].append(rm[m])
            bk[m].append(rm[m])
    overall = {m: round(statistics.fmean(v), 4) for m, v in agg.items()}
    kinds = {
        kind: {m: round(statistics.fmean(v), 4) for m, v in mv.items()}
        for kind, mv in sorted(by_kind.items())
    }
    return {"overall": overall, "by_kind": kinds, "n": len(gold)}


def _embed_queries(gold: list[dict], keyless: bool) -> dict[str, list[float]]:
    return {r["query"]: embed(r["query"], keyless=keyless) for r in {row["query"]: row for row in gold}.values()}


def _md_table(headers: list[str], rows: list[list[str]]) -> str:
    line = lambda cells: "| " + " | ".join(cells) + " |"
    return "\n".join([line(headers), line(["---"] * len(headers))] + [line(r) for r in rows]) + "\n"


def run_sweep(gold: list[dict], keyless: bool) -> dict:
    qvecs = _embed_queries(gold, keyless)
    results = {name: score_config(gold, qvecs, cfg) for name, cfg in CONFIGS.items()}

    cols = ["hit@5", "recall@5", "recall@10", "mrr@10"]
    headers = ["config"] + cols
    table = [[name] + [f"{results[name]['overall'][c]:.3f}" for c in cols] for name in CONFIGS]
    counts = {k: sum(1 for r in gold if r.get("kind", "paraphrase") == k) for k in ("paraphrase", "exact", "multi")}

    md = [f"# Retrieval sweep (n={len(gold)} gold queries)\n",
          f"Mix: {counts['paraphrase']} paraphrase · {counts['exact']} exact-token · {counts['multi']} multi-page\n",
          "## Overall\n", _md_table(headers, table)]
    # By-kind hit@5 — the honest story (dense on paraphrase, lexical on exact).
    kinds = sorted({k for r in results.values() for k in r["by_kind"]})
    bk_headers = ["config"] + [f"hit@5 ({k})" for k in kinds]
    bk_rows = [[name] + [f"{results[name]['by_kind'].get(k, {}).get('hit@5', float('nan')):.3f}" for k in kinds] for name in CONFIGS]
    md += ["## hit@5 by query kind\n", _md_table(bk_headers, bk_rows)]
    SWEEP_MD.write_text("\n".join(md), encoding="utf-8", newline="\n")

    print(f"sweep over {len(gold)} queries  ({counts})")
    print(_md_table(headers, table))
    REPORT_PATH.write_text(json.dumps({"n": len(gold), "sweep": results, "counts": counts}, indent=2), encoding="utf-8", newline="\n")
    return results


def run_shipped(gold: list[dict], keyless: bool, gate: bool) -> dict:
    qvecs = _embed_queries(gold, keyless)
    res = score_config(gold, qvecs, CONFIGS[SHIPPED])
    summary = res["overall"]
    print(f"eval: {len(gold)} queries · config={SHIPPED}")
    for m in METRIC_NAMES:
        print(f"  {m:10s} {summary[m]:.4f}")

    cols = ["hit@5", "recall@5", "recall@10", "mrr@10"]
    METRICS_MD.write_text(
        f"## Retrieval eval — `{SHIPPED}` (n={len(gold)})\n\n" + _md_table(cols, [[f"{summary[c]:.3f}" for c in cols]]),
        encoding="utf-8", newline="\n",
    )

    report = {"n": len(gold), "config": SHIPPED, "summary": summary, "by_kind": res["by_kind"]}
    if gate:
        baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
        tol = float(baseline.get("tolerance", 0.05))
        regressions = [
            f"{m}={summary[m]:.3f} < {baseline[m]} - {tol}"
            for m in baseline
            if m not in ("tolerance", "config") and m in summary and summary[m] < baseline[m] - tol
        ]
        report["gate"] = {"passed": not regressions, "regressions": regressions}
        print("gate: PASS" if not regressions else "gate: FAIL (regression vs baseline)")
        for r in regressions:
            print("  - " + r)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8", newline="\n")
    return report


def main(argv: list[str]) -> int:
    gold = load_gold()
    if not gold:
        print("no reviewed gold rows; nothing to score.")
        return 0
    keyless = "--keyless" in argv
    if "--sweep" in argv:
        run_sweep(gold, keyless)
        return 0
    report = run_shipped(gold, keyless, gate="--gate" in argv)
    if "--gate" in argv and not report.get("gate", {}).get("passed", True):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
