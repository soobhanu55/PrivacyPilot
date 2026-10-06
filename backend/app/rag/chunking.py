"""Chunking strategies compared in eval/eval_chunking.py. Each is a function text -> list[str]."""
from __future__ import annotations

import re
from typing import Callable

import numpy as np

Chunker = Callable[[str], list[str]]


def whole_article(text: str) -> list[str]:
    return [text]


def split_sentences(text: str) -> list[str]:
    """Legal text: split after '.' or ';' followed by whitespace (keeps '(a)' list items together with their lead-in)."""
    return [s for s in re.split(r"(?<=[.;])\s+", text) if s.strip()]


def semantic_chunks(text: str, embedder, percentile: float = 25, max_words: int = 300) -> list[str]:
    """Sentence-level semantic chunking: start a new chunk where the cosine similarity between neighbouring
    sentences is in the lowest `percentile` of this article's similarities, or when `max_words` is reached."""
    sents = split_sentences(text)
    if len(sents) < 3:
        return [text]
    emb = embedder.encode_passages(sents)
    sims = np.sum(emb[:-1] * emb[1:], axis=1)  # vectors are normalised
    cut = np.percentile(sims, percentile)
    chunks, cur, words = [], [sents[0]], len(sents[0].split())
    for s, sim in zip(sents[1:], sims):
        n = len(s.split())
        if sim < cut or words + n > max_words:
            chunks.append(" ".join(cur))
            cur, words = [], 0
        cur.append(s)
        words += n
    chunks.append(" ".join(cur))
    return chunks
