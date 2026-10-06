"""Test doubles, so the suite never downloads a model or calls a network service."""
import re
import zlib

import numpy as np


class FakeEmbedder:
    """Deterministic bag-of-words hashing embeddings (L2-normalised), same interface as E5Embedder."""

    def _vec(self, text: str) -> np.ndarray:
        v = np.zeros(128)
        for w in re.findall(r"\w+", text.lower()):
            v[zlib.crc32(w.encode()) % 128] += 1
        return v / (np.linalg.norm(v) + 1e-12)

    def encode_passages(self, texts):
        return np.vstack([self._vec(t) for t in texts])

    def encode_query(self, text):
        return self._vec(text)


class FixedScorer:
    """Returns preset (score, chunk index) per obligation id; everything else scores 0."""

    name = "fixed"

    def __init__(self, scores: dict[str, float], thresholds):
        self.scores, self.thresholds = scores, thresholds

    def prepare(self, chunks):
        pass

    def best_match(self, ob, chunks):
        return (self.scores.get(ob.id, 0.0), 0 if chunks else -1)
