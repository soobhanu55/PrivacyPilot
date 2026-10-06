"""Regulation corpus: the EU AI Act, NIS2 and CSRD (official EUR-Lex text) as retrievable chunks.

The article text in app/data/regulations/*.json was scraped from EUR-Lex (CELEX ids and URLs are in each
file). GDPR/BDSG text is NOT in this corpus: only three paraphrased sample sentences exist for them
(sample-data/legal-corpus), so GDPR obligations are cited by article number, not retrieved from text.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from app.rag.hybrid_retriever import RetrievedDoc

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "regulations"
FILES = {"AI Act": "ai_act_articles.json", "NIS2": "nis2_articles.json", "CSRD": "csrd_articles.json"}


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", text.replace("\xa0", " ")).strip()


def chunk_words(text: str, size: int = 250, overlap: int = 40) -> list[str]:
    """Overlapping word windows; an article shorter than `size` words stays one chunk."""
    words = text.split()
    if len(words) <= size:
        return [" ".join(words)]
    step = size - overlap
    return [" ".join(words[i:i + size]) for i in range(0, len(words) - overlap, step)]


def load_regulation_chunks(size: int = 250, regulations: list[str] | None = None, chunker=None) -> list[RetrievedDoc]:
    """One RetrievedDoc per chunk, each tagged with regulation, article number and article title.
    The title is prepended to the chunk text because it is the most informative few words of an article.
    `chunker` (text -> list[str]) overrides the default word windows of `size`; see app/rag/chunking.py."""
    docs: list[RetrievedDoc] = []
    for regulation, filename in FILES.items():
        if regulations and regulation not in regulations:
            continue
        data = json.loads((DATA_DIR / filename).read_text(encoding="utf-8"))
        for art in data["articles"]:
            number = int(re.search(r"\d+", art["heading"]).group())
            title = clean(art["title"]).strip("`' ")
            for i, chunk in enumerate(chunker(clean(art["body"])) if chunker else chunk_words(clean(art["body"]), size)):
                docs.append(RetrievedDoc(
                    id=f"{regulation}-art{number}-{i}",
                    text=f"{regulation} Article {number}: {title}. {chunk}",
                    metadata={"regulation": regulation, "article": number, "article_title": title, "chunk": i},
                    score=0.0,
                ))
    return docs


def article_title(regulation: str, article: int) -> str | None:
    for d in load_regulation_chunks(regulations=[regulation]):
        if d.metadata["article"] == article:
            return d.metadata["article_title"]
    return None
