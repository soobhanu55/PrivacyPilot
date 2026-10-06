import pytest

from app.rag.corpus import article_title, chunk_words, load_regulation_chunks
from app.rag.hybrid_retriever import HybridRetriever, RetrievedDoc
from eval.retrieval_questions import QUESTIONS
from tests.fakes import FakeEmbedder


@pytest.fixture(scope="module")
def corpus():
    return load_regulation_chunks()


# ---- corpus ------------------------------------------------------------------

def test_corpus_covers_the_three_regulations_with_article_metadata(corpus):
    assert {d.metadata["regulation"] for d in corpus} == {"AI Act", "NIS2", "CSRD"}
    assert len(corpus) > 500 and all(isinstance(d.metadata["article"], int) for d in corpus)
    assert article_title("AI Act", 14) == "Human oversight"
    assert article_title("NIS2", 23) == "Reporting obligations"
    assert article_title("NIS2", 9999) is None


def test_chunk_words_overlaps_and_short_text_stays_whole():
    assert chunk_words("a b c", size=10) == ["a b c"]
    chunks = chunk_words(" ".join(f"w{i}" for i in range(500)), size=100, overlap=20)
    assert chunks[0].split()[80:] == chunks[1].split()[:20]


def test_every_labelled_question_points_at_an_article_that_exists(corpus):
    """Guards against typos in the hand-labelled evaluation set."""
    existing = {(d.metadata["regulation"], d.metadata["article"]) for d in corpus}
    assert len(QUESTIONS) >= 30 and len({q for q, _, _ in QUESTIONS}) == len(QUESTIONS)
    for question, lang, accepted in QUESTIONS:
        assert lang in ("en", "de") and accepted and set(accepted) <= existing, question


# ---- retriever ----------------------------------------------------------------

def small_index(embedder=None, reranker=None):
    docs = [
        RetrievedDoc("a", "human oversight of high risk ai systems", {"reg": "AI"}, 0.0),
        RetrievedDoc("b", "reporting of incidents within 24 hours", {"reg": "NIS2"}, 0.0),
        RetrievedDoc("c", "penalties and administrative fines", {"reg": "NIS2"}, 0.0),
    ]
    r = HybridRetriever(embedder=embedder, reranker=reranker)
    r.index(docs)
    return r


def test_bm25_finds_the_right_article_in_the_real_corpus(corpus):
    r = HybridRetriever()
    r.index(corpus)
    top = r.retrieve("human oversight of high-risk AI systems", top_k=3)
    assert top[0].metadata["regulation"] == "AI Act" and top[0].metadata["article"] == 14


def test_default_mode_is_bm25_without_an_embedder_and_dense_with_one():
    assert small_index().retrieve("incidents 24 hours", top_k=1)[0].id == "b"
    r = small_index(embedder=FakeEmbedder())
    assert r.retrieve("incidents 24 hours", top_k=1)[0].id == "b"
    assert 0 < r.retrieve("incidents 24 hours", top_k=1, mode="dense")[0].score <= 1.0001  # cosine


def test_modes_whose_component_is_missing_raise_instead_of_degrading():
    r = small_index()
    for mode in ("dense", "hybrid"):
        with pytest.raises(RuntimeError):
            r.retrieve("x", mode=mode)
    with pytest.raises(RuntimeError):
        small_index(embedder=FakeEmbedder()).retrieve("x", mode="hybrid_rerank")
    with pytest.raises(ValueError):
        r.retrieve("x", mode="magic")


def test_hybrid_fuses_both_rankings():
    r = small_index(embedder=FakeEmbedder())
    top = r.retrieve("human oversight systems", top_k=3, mode="hybrid")
    assert top[0].id == "a" and len(top) == 3


def test_rerank_reorders_by_the_reranker_score():
    class Prefer:  # scores 'penalties' highest regardless of the query
        def score(self, query, texts):
            return [1.0 if "penalties" in t else 0.0 for t in texts]

    r = small_index(embedder=FakeEmbedder(), reranker=Prefer())
    assert r.retrieve("incidents", top_k=1, mode="hybrid_rerank")[0].id == "c"


def test_metadata_filter_restricts_candidates():
    r = small_index()
    assert {d.id for d in r.retrieve("systems incidents penalties", metadata_filter={"reg": "NIS2"})} == {"b", "c"}
    assert r.retrieve("anything", metadata_filter={"reg": "nope"}) == []


class _FakeEmbedder:
    """One axis per sentence topic so neighbouring sentences on different topics have similarity 0."""

    def encode_passages(self, texts):
        import numpy as np

        return np.array([[1.0, 0.0] if "alpha" in t else [0.0, 1.0] for t in texts])


def test_semantic_chunks_split_at_topic_change():
    from app.rag.chunking import semantic_chunks

    text = "alpha one. alpha two. alpha three. beta one. beta two. beta three."
    chunks = semantic_chunks(text, _FakeEmbedder(), percentile=10)
    assert chunks == ["alpha one. alpha two. alpha three.", "beta one. beta two. beta three."]
    assert semantic_chunks("one. two.", _FakeEmbedder()) == ["one. two."]


def test_custom_chunker_changes_chunk_count():
    from app.rag.chunking import whole_article

    assert len(load_regulation_chunks(chunker=whole_article)) < len(load_regulation_chunks(size=60))
