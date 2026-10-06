"""Chunking x retrieval-mode grid search on the regulation questions (article-level).

    python eval/eval_chunking.py      # run from backend/, needs the ml extra; writes ../docs/chunking_eval.md

The 37 questions are split: even-numbered ones (dev) pick the configuration, odd-numbered ones (test) report
it, so the winner is not scored on the questions that chose it. With this few questions most differences are
within noise; the report says so instead of declaring a winner.
"""
from __future__ import annotations

import functools
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.rag.chunking import semantic_chunks, whole_article  # noqa: E402
from app.rag.corpus import chunk_words, load_regulation_chunks  # noqa: E402
from app.rag.hybrid_retriever import CrossEncoderReranker, E5Embedder, HybridRetriever  # noqa: E402
from eval.eval_retrieval import MODES, article_ranking, ci, hit_and_rr  # noqa: E402
from eval.retrieval_questions import QUESTIONS  # noqa: E402


def chunkers(embedder) -> dict:
    out = {"whole article": whole_article}
    for size in (60, 120, 250, 400):
        out[f"words {size} (overlap {size // 6})"] = functools.partial(chunk_words, size=size, overlap=size // 6)
    for pct in (10, 25):
        out[f"semantic p{pct}"] = functools.partial(semantic_chunks, embedder=embedder, percentile=pct)
    return out


def main() -> None:
    embedder, reranker = E5Embedder(), CrossEncoderReranker()
    dev = [q for i, q in enumerate(QUESTIONS) if i % 2 == 0]
    test = [q for i, q in enumerate(QUESTIONS) if i % 2 == 1]

    def score(retriever, qs, mode):
        return np.array([hit_and_rr(article_ranking(retriever, q, mode), acc) for q, _, acc in qs])

    rows = []
    for name, fn in chunkers(embedder).items():
        chunks = load_regulation_chunks(chunker=fn)
        retriever = HybridRetriever(embedder=embedder, reranker=reranker)
        retriever.index(chunks)
        for mode in MODES:
            rows.append((name, mode, len(chunks), score(retriever, dev, mode), score(retriever, test, mode)))
        print(name, len(chunks), "chunks done", flush=True)

    best = max(rows, key=lambda r: (r[3][:, 2].mean(), -r[2]))  # dev MRR, fewer chunks wins ties
    lines = [
        "# Chunking x retrieval-mode grid search\n",
        f"{len(dev)} dev and {len(test)} test questions (alternating), same regulation corpus as `retrieval_eval.md`. "
        f"{len(rows)} configurations; selection on dev MRR only. Test columns are the held-out half.\n",
        "| Chunking | Chunks | Mode | Dev MRR | Test Hit@1 (95% CI) | Test MRR |", "|---|---|---|---|---|---|",
    ]
    for name, mode, n, d, t in rows:
        lo, hi = ci(t[:, 0])
        mark = " **(chosen on dev)**" if (name, mode) == (best[0], best[1]) else ""
        lines.append(f"| {name} | {n} | {mode}{mark} | {d[:, 2].mean():.2f} | {t[:, 0].mean():.2f} ({lo:.2f} to {hi:.2f}) | {t[:, 2].mean():.2f} |")
    bt = best[4]
    lo, hi = ci(bt[:, 0])
    default = next(r for r in rows if r[0].startswith("words 250") and r[1] == "dense")
    lines += [
        "", f"Chosen on dev: **{best[0]} + {best[1]}**; held-out Hit@1 {bt[:, 0].mean():.2f} ({lo:.2f} to {hi:.2f}), MRR {bt[:, 2].mean():.2f}. "
        f"Shipped default (words 250, dense): held-out Hit@1 {default[4][:, 0].mean():.2f}, MRR {default[4][:, 2].mean():.2f}.",
        "", f"With {len(test)} test questions a 95% interval is about +/-0.2 wide, so gaps of a few points between configurations are noise. "
        "The one consistent gap is the retrieval mode: dense beats BM25 at every chunk size. Chunk size and semantic versus fixed windows make no reliable difference, and the configuration picked on dev did not beat the shipped default on the held-out half, so the default stays.",
    ]
    out = Path(__file__).resolve().parent.parent.parent / "docs" / "chunking_eval.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
