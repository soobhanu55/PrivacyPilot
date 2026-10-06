"""Evaluate the retrieval modes on the hand-labelled regulation questions (article-level).

    python eval/eval_retrieval.py      # run from backend/, needs the ml extra; writes ../docs/retrieval_eval.md

Replaces the old 20-question eval, where every question had 3 candidates (1 right, 2 unrelated) and random
chance was already 33%. Here the pool is all 178 distinct articles and random Hit@1 is about 0.6%.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval.retrieval_questions import QUESTIONS  # noqa: E402
from app.rag.corpus import load_regulation_chunks  # noqa: E402
from app.rag.hybrid_retriever import CrossEncoderReranker, E5Embedder, HybridRetriever  # noqa: E402

MODES = ["bm25", "dense", "hybrid", "hybrid_rerank"]
K_CHUNKS = 60  # chunks fetched per question before collapsing to articles


def article_ranking(retriever: HybridRetriever, question: str, mode: str) -> list[tuple[str, int]]:
    """Chunk ranking collapsed to a ranking of distinct articles (first appearance wins)."""
    seen: list[tuple[str, int]] = []
    for doc in retriever.retrieve(question, top_k=K_CHUNKS, mode=mode):
        key = (doc.metadata["regulation"], doc.metadata["article"])
        if key not in seen:
            seen.append(key)
    return seen


def hit_and_rr(ranking: list, accepted: list, k: int = 5) -> tuple[float, float, float]:
    first = next((i + 1 for i, a in enumerate(ranking) if a in accepted), None)
    return float(first == 1), float(first is not None and first <= k), (1 / first if first else 0.0)


def ci(values: np.ndarray, n: int = 2000, seed: int = 0) -> tuple[float, float]:
    rng = np.random.default_rng(seed)
    m = [rng.choice(values, len(values)).mean() for _ in range(n)]
    return float(np.percentile(m, 2.5)), float(np.percentile(m, 97.5))


def main() -> None:
    chunks = load_regulation_chunks()
    n_articles = len({(d.metadata["regulation"], d.metadata["article"]) for d in chunks})
    retriever = HybridRetriever(embedder=E5Embedder(), reranker=CrossEncoderReranker())
    retriever.index(chunks)

    results = {m: [] for m in MODES}
    for q, lang, accepted in QUESTIONS:
        for m in MODES:
            results[m].append(hit_and_rr(article_ranking(retriever, q, m), accepted))
    langs = np.array([lang for _, lang, _ in QUESTIONS])

    random_hit1 = float(np.mean([len(acc) / n_articles for _, _, acc in QUESTIONS]))
    lines = [
        "# Retrieval evaluation (article level)\n",
        f"{len(QUESTIONS)} hand-labelled questions ({int((langs == 'en').sum())} English, {int((langs == 'de').sum())} German) "
        f"against {n_articles} articles of the AI Act, NIS2 and CSRD ({len(chunks)} chunks). "
        f"Random ranking would hit rank 1 about {random_hit1:.1%} of the time. Embeddings: "
        f"`{E5Embedder().model_name}`; reranker: `{CrossEncoderReranker().model_name}` (English-only).\n",
        "| Mode | Hit@1 (95% CI) | Hit@5 | MRR | Hit@1 English | Hit@1 German |", "|---|---|---|---|---|---|",
    ]
    for m in MODES:
        arr = np.array(results[m])
        lo, hi = ci(arr[:, 0])
        lines.append(f"| {m} | {arr[:, 0].mean():.2f} ({lo:.2f} to {hi:.2f}) | {arr[:, 1].mean():.2f} | {arr[:, 2].mean():.2f} "
                     f"| {arr[langs == 'en', 0].mean():.2f} | {arr[langs == 'de', 0].mean():.2f} |")
    text = "\n".join(lines) + "\n"
    out = Path(__file__).resolve().parent.parent.parent / "docs" / "retrieval_eval.md"
    out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
