"""Evaluate the gap analysis on synthetic documents with known ground truth.

    python eval/eval_gap_analysis.py     # from backend/, needs the ml extra; writes ../docs/gap_eval.md

Thresholds are tuned on the DEV split only; results are reported on the TEST split, whose paragraph wordings
the tuning never saw. The documents are synthetic and written by the author, so these numbers measure the
matcher on these paraphrases, not on real SME policies (see eval/synthetic_policies.py).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.synthetic_policies import OBLIGATION_IDS, make_documents  # noqa: E402
from app.rag.hybrid_retriever import E5Embedder  # noqa: E402
from app.services.gap_analysis import OBLIGATIONS, DenseScorer, KeywordScorer, Thresholds, applies, split_into_chunks  # noqa: E402

N_DOCS = 60
BY_ID = {o.id: o for o in OBLIGATIONS}


def collect(scorer, docs: list[dict]) -> dict:
    """Scores for applicable (document, obligation) pairs, with truth, plus applicability accuracy."""
    scores, truth, app_ok, app_total = [], [], 0, 0
    for d in docs:
        chunks = split_into_chunks(d["text"])
        scorer.prepare(chunks)
        for ob_id in OBLIGATION_IDS:
            ob = BY_ID[ob_id]
            if ob.applies_if is not None:  # does the trigger fire exactly when the topic is mentioned?
                app_total += 1
                app_ok += applies(ob, chunks) == d["mentioned"][ob_id]
            if not applies(ob, chunks):
                continue
            score, _ = scorer.best_match(ob, chunks)
            scores.append(score)
            truth.append(d["present"][ob_id])
    return {"scores": np.array(scores), "truth": np.array(truth), "app_acc": app_ok / max(app_total, 1)}


def prf(pred: np.ndarray, truth: np.ndarray) -> tuple[float, float, float]:
    tp = int((pred & truth).sum())
    p = tp / max(int(pred.sum()), 1)
    r = tp / max(int(truth.sum()), 1)
    return p, r, (2 * p * r / (p + r) if p + r else 0.0)


def tune(scores: np.ndarray, truth: np.ndarray, target_precision: float = 0.9, target_recall: float = 0.95) -> Thresholds:
    """Safety-first thresholds on the dev split. found = lowest threshold whose 'found' calls are >=90% precise
    (a false 'found' is false assurance, the costly error); falls back to best F1 if that is unreachable.
    review = highest threshold at or below it that still keeps >=95% of truly evidenced items out of 'gap'."""
    cands = np.unique(scores)
    ok = [t for t in cands if prf(scores >= t, truth)[0] >= target_precision]
    found = min(ok) if ok else max(cands, key=lambda t: (prf(scores >= t, truth)[2], t))
    review = max((t for t in cands if t <= found and (scores[truth] >= t).mean() >= target_recall), default=found)
    return Thresholds(found=float(found), review=float(review))


def row(name: str, d: dict, th: Thresholds) -> str:
    s, y = d["scores"], d["truth"]
    p, r, f1 = prf(s >= th.found, y)
    in_review = (s >= th.review) & (s < th.found)
    return (f"| {name} | {p:.2f} | {r:.2f} | {f1:.2f} | {(s >= th.review)[y].mean():.2f} | "
            f"{in_review[~y].mean():.2f} | {in_review.mean():.2f} |")


def main() -> None:
    dev, test = make_documents("dev", N_DOCS), make_documents("test", N_DOCS)
    out = ["# Gap analysis evaluation (synthetic documents)\n",
           f"{N_DOCS} dev and {N_DOCS} test documents, each with 10 obligations present (50%), mentioned but unmet (25%) or absent (25%) "
           "plus filler; German and English. **Synthetic, written by the author:** this measures the matcher on these "
           "paraphrases, not on real company policies. Thresholds are tuned on dev only; the table is the unseen test split.\n"]
    tuned = {}
    for scorer in (KeywordScorer(), DenseScorer(E5Embedder())):
        d_dev, d_test = collect(scorer, dev), collect(scorer, test)
        th = tune(d_dev["scores"], d_dev["truth"])
        tuned[scorer.name] = th
        prevalence = d_test["truth"].mean()
        out += [
            f"## {scorer.name}\n",
            f"Tuned on dev: found >= {th.found:.3f}, review >= {th.review:.3f}. Test pairs: {len(d_test['truth'])} "
            f"({prevalence:.0%} truly evidenced). Applicability trigger accuracy (test): {d_test['app_acc']:.2f}.\n",
            "| Setting (test split) | Precision of 'found' | Recall of 'found' | F1 | Recall found+review | Unmet items sent to review | Share of all items in review |",
            "|---|---|---|---|---|---|---|",
            row("tuned thresholds", d_test, th),
            f"| always 'gap' | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 | 0.00 |",
            f"| always 'found' | {prevalence:.2f} | 1.00 | {2 * prevalence / (1 + prevalence):.2f} | 1.00 | 0.00 | 0.00 |",
            "",
        ]
        print(scorer.name, "tuned:", th)
    out += [
        "## What was tried, including what did not work\n",
        "- **German-only queries (first version):** English passages scored lower than German ones regardless of meaning, so a German distractor "
        "(\"we have not appointed a DPO\") scored about the same as an English genuine passage and no single threshold worked "
        "(test recall of found+review was well below target). Fixed by scoring against a German and an English query and keeping the better match.",
        "- **First threshold rule had a bug:** it picked the lowest review threshold instead of the highest, which sent 72 to 75% of all items to review. "
        "Corrected, and the objective changed to a precision target (a false 'found' is false assurance).",
        "- **Small-LLM verifier (Qwen2.5-1.5B-Instruct, zero-shot yes/no on the top-3 passages):** worse than plain similarity "
        "(test AUC 0.61 vs 0.87), so it was dropped.",
        "- **Limits that remain:** thresholds tuned on one set of wordings recover only 78% of evidenced items on unseen wordings (found+review), "
        "so 'gap' means 'no evidence found', not 'proven absent'. A passage that mentions an obligation negatively is the hard case.",
        "",
    ]
    text = "\n".join(out)
    (Path(__file__).resolve().parent.parent.parent / "docs" / "gap_eval.md").write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
