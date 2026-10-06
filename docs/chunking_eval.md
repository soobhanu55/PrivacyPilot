# Chunking x retrieval-mode grid search

19 dev and 18 test questions (alternating), same regulation corpus as `retrieval_eval.md`. 28 configurations; selection on dev MRR only. Test columns are the held-out half.

| Chunking | Chunks | Mode | Dev MRR | Test Hit@1 (95% CI) | Test MRR |
|---|---|---|---|---|---|
| whole article | 191 | bm25 | 0.66 | 0.72 (0.50 to 0.89) | 0.78 |
| whole article | 191 | dense | 0.89 | 1.00 (1.00 to 1.00) | 1.00 |
| whole article | 191 | hybrid | 0.81 | 0.83 (0.67 to 1.00) | 0.86 |
| whole article | 191 | hybrid_rerank | 0.78 | 0.83 (0.67 to 1.00) | 0.89 |
| words 60 (overlap 10) | 1991 | bm25 | 0.68 | 0.61 (0.39 to 0.83) | 0.72 |
| words 60 (overlap 10) | 1991 | dense **(chosen on dev)** | 0.95 | 0.94 (0.83 to 1.00) | 0.97 |
| words 60 (overlap 10) | 1991 | hybrid | 0.84 | 0.78 (0.56 to 0.94) | 0.86 |
| words 60 (overlap 10) | 1991 | hybrid_rerank | 0.87 | 0.72 (0.50 to 0.89) | 0.83 |
| words 120 (overlap 20) | 1032 | bm25 | 0.62 | 0.78 (0.56 to 0.94) | 0.81 |
| words 120 (overlap 20) | 1032 | dense | 0.89 | 1.00 (1.00 to 1.00) | 1.00 |
| words 120 (overlap 20) | 1032 | hybrid | 0.87 | 0.83 (0.67 to 1.00) | 0.88 |
| words 120 (overlap 20) | 1032 | hybrid_rerank | 0.93 | 0.78 (0.56 to 0.94) | 0.84 |
| words 250 (overlap 41) | 535 | bm25 | 0.64 | 0.78 (0.56 to 0.94) | 0.81 |
| words 250 (overlap 41) | 535 | dense | 0.88 | 1.00 (1.00 to 1.00) | 1.00 |
| words 250 (overlap 41) | 535 | hybrid | 0.90 | 0.78 (0.56 to 0.94) | 0.85 |
| words 250 (overlap 41) | 535 | hybrid_rerank | 0.86 | 0.78 (0.56 to 0.94) | 0.84 |
| words 400 (overlap 66) | 367 | bm25 | 0.66 | 0.67 (0.44 to 0.89) | 0.75 |
| words 400 (overlap 66) | 367 | dense | 0.87 | 1.00 (1.00 to 1.00) | 1.00 |
| words 400 (overlap 66) | 367 | hybrid | 0.81 | 0.83 (0.67 to 1.00) | 0.88 |
| words 400 (overlap 66) | 367 | hybrid_rerank | 0.79 | 0.89 (0.72 to 1.00) | 0.92 |
| semantic p10 | 762 | bm25 | 0.65 | 0.83 (0.67 to 1.00) | 0.84 |
| semantic p10 | 762 | dense | 0.91 | 0.83 (0.67 to 1.00) | 0.92 |
| semantic p10 | 762 | hybrid | 0.83 | 0.83 (0.67 to 1.00) | 0.87 |
| semantic p10 | 762 | hybrid_rerank | 0.90 | 0.83 (0.67 to 1.00) | 0.88 |
| semantic p25 | 1235 | bm25 | 0.58 | 0.72 (0.50 to 0.89) | 0.78 |
| semantic p25 | 1235 | dense | 0.91 | 0.89 (0.72 to 1.00) | 0.94 |
| semantic p25 | 1235 | hybrid | 0.87 | 0.83 (0.67 to 1.00) | 0.87 |
| semantic p25 | 1235 | hybrid_rerank | 0.93 | 0.83 (0.67 to 1.00) | 0.87 |

Chosen on dev: **words 60 (overlap 10) + dense**; held-out Hit@1 0.94 (0.83 to 1.00), MRR 0.97. Shipped default (words 250, dense): held-out Hit@1 1.00, MRR 1.00.

With 18 test questions a 95% interval is about +/-0.2 wide, so gaps of a few points between configurations are noise. The one consistent gap is the retrieval mode: dense beats BM25 at every chunk size. Chunk size and semantic versus fixed windows make no reliable difference, and the configuration picked on dev did not beat the shipped default on the held-out half, so the default stays.
