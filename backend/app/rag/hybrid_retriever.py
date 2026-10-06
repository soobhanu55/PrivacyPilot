"""Hybrid retrieval: BM25 + dense embeddings fused with reciprocal-rank fusion, plus an optional
cross-encoder reranker. Dense search and reranking are optional (injected), so the lexical path always
works without a model; asking for a mode whose component is missing raises instead of silently degrading.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Protocol

import numpy as np
from rank_bm25 import BM25Okapi

MODES = ("bm25", "dense", "hybrid", "hybrid_rerank")
RRF_K = 60  # standard reciprocal-rank-fusion constant
RERANK_DEPTH = 20  # how many fused candidates the cross-encoder re-scores


@dataclass
class RetrievedDoc:
    id: str
    text: str
    metadata: dict[str, Any]
    score: float


class Embedder(Protocol):
    def encode_passages(self, texts: list[str]) -> np.ndarray: ...
    def encode_query(self, text: str) -> np.ndarray: ...


class Reranker(Protocol):
    def score(self, query: str, texts: list[str]) -> list[float]: ...


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def _ranks(scores: np.ndarray) -> np.ndarray:
    """Rank of each item, 1 = best (stable for ties)."""
    ranks = np.empty(len(scores), dtype=int)
    ranks[np.argsort(-scores, kind="stable")] = np.arange(1, len(scores) + 1)
    return ranks


class E5Embedder:
    """Local multilingual-e5 embeddings (needs the optional `ml` extra: sentence-transformers).
    e5 models expect 'query: ' / 'passage: ' prefixes. Vectors are L2-normalised, so dot product = cosine."""

    def __init__(self, model_name: str | None = None):
        self.model_name = model_name or os.environ.get("EMBEDDING_MODEL", "intfloat/multilingual-e5-large")

    @property
    @lru_cache
    def _model(self):
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(self.model_name)

    def encode_passages(self, texts: list[str]) -> np.ndarray:
        return np.asarray(self._model.encode([f"passage: {t}" for t in texts], normalize_embeddings=True,
                                             show_progress_bar=False))

    def encode_query(self, text: str) -> np.ndarray:
        return np.asarray(self._model.encode([f"query: {text}"], normalize_embeddings=True,
                                             show_progress_bar=False))[0]


class CrossEncoderReranker:
    """ms-marco MiniLM cross-encoder (English). Loaded once, not per call."""

    def __init__(self, model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"):
        self.model_name = model_name

    @property
    @lru_cache
    def _model(self):
        from sentence_transformers import CrossEncoder

        return CrossEncoder(self.model_name)

    def score(self, query: str, texts: list[str]) -> list[float]:
        return [float(s) for s in self._model.predict([[query, t] for t in texts], show_progress_bar=False)]


class HybridRetriever:
    def __init__(self, embedder: Embedder | None = None, reranker: Reranker | None = None) -> None:
        self.embedder, self.reranker = embedder, reranker
        self._docs: list[RetrievedDoc] = []
        self._bm25: BM25Okapi | None = None
        self._emb: np.ndarray | None = None

    def index(self, docs: list[RetrievedDoc]) -> None:
        self._docs = docs
        self._bm25 = BM25Okapi([tokenize(d.text) for d in docs]) if docs else None
        self._emb = self.embedder.encode_passages([d.text for d in docs]) if (docs and self.embedder) else None

    def _scores(self, query: str, mode: str) -> np.ndarray:
        if mode == "bm25":
            return np.asarray(self._bm25.get_scores(tokenize(query)))
        if self._emb is None:
            raise RuntimeError(f"mode {mode!r} needs an embedder; none was provided")
        return self._emb @ self.embedder.encode_query(query)

    def retrieve(self, query: str, metadata_filter: dict[str, Any] | None = None, top_k: int = 8,
                 mode: str | None = None) -> list[RetrievedDoc]:
        """mode=None picks 'dense' when an embedder is present, else 'bm25'. Dense is the default because it
        scored best on the regulation questions (docs/retrieval_eval.md): fusing in BM25 or adding the
        English-only cross-encoder lowered Hit@1. An explicit mode whose component is missing raises."""
        mode = mode or ("dense" if self.embedder else "bm25")
        if mode not in MODES:
            raise ValueError(f"unknown mode {mode!r}, expected one of {MODES}")
        if mode == "hybrid_rerank" and self.reranker is None:
            raise RuntimeError("mode 'hybrid_rerank' needs a reranker; none was provided")
        metadata_filter = metadata_filter or {}
        keep = [i for i, d in enumerate(self._docs)
                if all(str(d.metadata.get(k)) == str(v) for k, v in metadata_filter.items())]
        if not keep or self._bm25 is None:
            return []

        if mode == "bm25":
            scores = self._scores(query, "bm25")[keep]
        elif mode == "dense":
            scores = self._scores(query, "dense")[keep]
        else:  # hybrid / hybrid_rerank: BM25 and dense, fused by rank
            lexical = self._scores(query, "bm25")[keep]
            scores = 1 / (RRF_K + _ranks(lexical)) + 1 / (RRF_K + _ranks(self._scores(query, "dense")[keep]))

        order = np.argsort(-scores, kind="stable")
        if mode == "hybrid_rerank":
            head = order[:RERANK_DEPTH]
            ce = self.reranker.score(query, [self._docs[keep[j]].text for j in head])
            order = head[np.argsort(-np.asarray(ce), kind="stable")]
            scores = np.zeros(len(keep))
            scores[head] = ce
        return [RetrievedDoc(id=self._docs[keep[j]].id, text=self._docs[keep[j]].text,
                             metadata=self._docs[keep[j]].metadata, score=float(scores[j]))
                for j in order[:top_k]]
