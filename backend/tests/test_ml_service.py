from app.services.ml_service import rerank_candidates


def test_rerank_candidates_returns_top_k() -> None:
    results = rerank_candidates(
        query="consent retention policy",
        candidates=[
            "No consent register exists.",
            "Data retention policy is documented.",
            "Office kitchen menu update.",
        ],
        top_k=2,
    )
    assert len(results) == 2
    assert "text" in results[0]
    assert "score" in results[0]
