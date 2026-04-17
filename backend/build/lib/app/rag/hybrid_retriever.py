from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rank_bm25 import BM25Okapi


@dataclass
class RetrievedDoc:
    id: str
    text: str
    metadata: dict[str, Any]
    score: float


class HybridRetriever:
    """Hybrid retriever stub with BM25 + dense placeholder + rerank hook."""

    def __init__(self) -> None:
        self._docs: list[RetrievedDoc] = []
        self._bm25: BM25Okapi | None = None

    def index(self, docs: list[RetrievedDoc]) -> None:
        self._docs = docs
        tokenized = [doc.text.lower().split() for doc in docs]
        self._bm25 = BM25Okapi(tokenized) if tokenized else None

    def retrieve(self, query: str, metadata_filter: dict[str, str] | None = None, top_k: int = 8) -> list[RetrievedDoc]:
        metadata_filter = metadata_filter or {}
        filtered = [
            doc
            for doc in self._docs
            if all(str(doc.metadata.get(k)) == str(v) for k, v in metadata_filter.items())
        ]
        if not filtered:
            return []
        local_bm25 = BM25Okapi([doc.text.lower().split() for doc in filtered])
        scores = local_bm25.get_scores(query.lower().split())
        ranked = sorted(
            [RetrievedDoc(id=d.id, text=d.text, metadata=d.metadata, score=float(s)) for d, s in zip(filtered, scores)],
            key=lambda item: item.score,
            reverse=True,
        )
        return self._cross_encoder_rerank(ranked[: top_k * 2], query)[:top_k]

    def _cross_encoder_rerank(self, docs: list[RetrievedDoc], query: str) -> list[RetrievedDoc]:
        query_terms = set(query.lower().split())
        reranked = sorted(docs, key=lambda d: len(query_terms.intersection(set(d.text.lower().split()))), reverse=True)
        return reranked
