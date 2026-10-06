from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache


@dataclass
class RankedCandidate:
    text: str
    score: float


def _lexical_score(query: str, candidate: str) -> float:
    q = set(query.lower().split())
    c = set(candidate.lower().split())
    if not q:
        return 0.0
    return len(q.intersection(c)) / len(q)


@lru_cache
def _cross_encoder():
    from sentence_transformers import CrossEncoder  # type: ignore

    return CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")  # loaded once, not on every request


def rerank_candidates(query: str, candidates: list[str], top_k: int = 3) -> list[dict]:
    """Rerank candidates using sentence-transformers when available, lexical fallback otherwise."""
    try:
        model = _cross_encoder()
        pairs = [[query, c] for c in candidates]
        scores = model.predict(pairs).tolist()
        ranked = sorted(
            [RankedCandidate(text=c, score=float(s)) for c, s in zip(candidates, scores)],
            key=lambda item: item.score,
            reverse=True,
        )
    except Exception:
        ranked = sorted(
            [RankedCandidate(text=c, score=_lexical_score(query, c)) for c in candidates],
            key=lambda item: item.score,
            reverse=True,
        )
    return [{"text": item.text, "score": round(item.score, 4)} for item in ranked[:top_k]]
