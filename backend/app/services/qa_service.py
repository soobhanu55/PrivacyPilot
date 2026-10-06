"""Question answering over the AI Act / NIS2 / CSRD corpus, with article citations.

Retrieval is local (dense e5 embeddings when sentence-transformers is installed, else BM25). An answer is
generated only when GROQ_API_KEY is set (Groq's free tier, OpenAI-compatible API); without a key the endpoint
still returns the retrieved articles. The key is read from the environment and never stored or logged.
"""
from __future__ import annotations

from functools import lru_cache

import httpx

from app.rag.corpus import load_regulation_chunks
from app.rag.hybrid_retriever import E5Embedder, HybridRetriever

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
SYSTEM_PROMPT = (
    "You answer questions about EU regulation using ONLY the numbered excerpts provided. Cite the source after each claim "
    "like [NIS2 Art. 23]. If the excerpts do not contain the answer, say you cannot tell from the excerpts. "
    "This is not legal advice."
)


@lru_cache
def regulation_retriever() -> HybridRetriever:
    try:
        embedder = E5Embedder()
        embedder.encode_query("test")  # fails fast if sentence-transformers or the model is unavailable
    except Exception:
        embedder = None
    retriever = HybridRetriever(embedder=embedder)
    retriever.index(load_regulation_chunks())
    return retriever


def retrieve_clauses(retriever: HybridRetriever, question: str, regulations: list[str], top_k: int) -> list[dict]:
    """Top articles (best chunk per article, one entry each) as {regulation, article, title, excerpt, score}."""
    # Filter BEFORE ranking (one pass per requested regulation, then merge by score); filtering the global top-N
    # afterwards would return nothing when the best matches all belong to another regulation.
    passes = [{"regulation": r} for r in regulations] or [None]
    hits = [d for flt in passes for d in retriever.retrieve(question, metadata_filter=flt, top_k=top_k * 6)]
    seen: dict[tuple[str, int], dict] = {}
    for doc in sorted(hits, key=lambda d: -d.score):
        m = doc.metadata
        key = (m["regulation"], m["article"])
        if key not in seen:
            seen[key] = {"regulation": m["regulation"], "article": m["article"], "title": m["article_title"],
                         "excerpt": doc.text[:600], "score": round(doc.score, 4)}
    return list(seen.values())[:top_k]


async def _groq_answer(question: str, clauses: list[dict], api_key: str, model: str,
                       client: httpx.AsyncClient | None = None) -> tuple[str | None, str | None]:
    context = "\n\n".join(f"[{i + 1}] {c['regulation']} Art. {c['article']} ({c['title']}): {c['excerpt']}"
                          for i, c in enumerate(clauses))
    body = {"model": model, "temperature": 0, "messages": [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Excerpts:\n{context}\n\nQuestion: {question}"}]}
    own = client is None
    client = client or httpx.AsyncClient(timeout=30)
    try:
        resp = await client.post(GROQ_URL, json=body, headers={"Authorization": f"Bearer {api_key}"})
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"], None
    except Exception as exc:  # the retrieved articles are still useful, so a failed generation is not an error
        return None, type(exc).__name__
    finally:
        if own:
            await client.aclose()


async def ask(question: str, regulations: list[str] | None = None, top_k: int = 5, *, retriever: HybridRetriever | None = None,
              groq_key: str | None = None, model: str = "openai/gpt-oss-120b", client: httpx.AsyncClient | None = None) -> dict:
    retriever = retriever or regulation_retriever()
    clauses = retrieve_clauses(retriever, question, regulations or [], top_k)
    answer, error = (None, None)
    if groq_key and clauses:
        answer, error = await _groq_answer(question, clauses, groq_key, model, client)
    return {"question": question, "clauses": clauses, "answer": answer, "generation_error": error,
            "retrieval": "dense" if retriever.embedder else "bm25"}
