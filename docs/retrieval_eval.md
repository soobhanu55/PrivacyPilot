# Retrieval evaluation (article level)

37 hand-labelled questions (32 English, 5 German) against 178 articles of the AI Act, NIS2 and CSRD (534 chunks). Random ranking would hit rank 1 about 0.6% of the time. Embeddings: `intfloat/multilingual-e5-large`; reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2` (English-only).

| Mode | Hit@1 (95% CI) | Hit@5 | MRR | Hit@1 English | Hit@1 German |
|---|---|---|---|---|---|
| bm25 | 0.68 (0.51 to 0.81) | 0.78 | 0.73 | 0.78 | 0.00 |
| dense | 0.89 (0.78 to 0.97) | 1.00 | 0.94 | 0.91 | 0.80 |
| hybrid | 0.81 (0.68 to 0.92) | 0.95 | 0.88 | 0.88 | 0.40 |
| hybrid_rerank | 0.78 (0.65 to 0.92) | 0.95 | 0.85 | 0.91 | 0.00 |
