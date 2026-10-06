# PrivacyPilot

Multi-tenant compliance SaaS for German SMEs. It reads a company's own policy documents, checks them against GDPR (DSGVO), NIS2 and EU AI Act obligations, and shows for each obligation either the passage that evidences it or "no evidence found", with article citations. It also answers regulation questions over the real AI Act / NIS2 / CSRD text.

## What it does

1. **Upload** TXT, Markdown, PDF or DOCX policy documents (per tenant, role-based access: owner / auditor / viewer).
2. **Analyze** (`POST /analyze-compliance`): the documents are actually read and split into passages; vendors are detected (US cloud tools are flagged as possible third-country transfers); 10 obligations are each matched to the best evidence passage; applicability is decided from the text (the transfer rule only applies if third-country vendors appear, the AI Act oversight rule only if AI is mentioned); the result is a severity-weighted score plus one finding per open obligation, citing the article.
3. **Ask** (`POST /ask`): question answering over the AI Act, NIS2 and CSRD (178 articles, official EUR-Lex text). Retrieval is local; an answer is generated only if a `GROQ_API_KEY` is set (Groq free tier), otherwise you get the retrieved articles.

Stack: FastAPI · Next.js · LangGraph · PostgreSQL/Alembic · Redis/Celery · multilingual-e5 embeddings · BM25 · Docker.

## Results

Both evaluations are reproducible (`python eval/eval_retrieval.py`, `python eval/eval_gap_analysis.py` from `backend/`, needs `pip install .[ml]`).

### Regulation retrieval (`docs/retrieval_eval.md`)

37 hand-labelled questions (32 English, 5 German) against 178 articles. Random ranking hits rank 1 about 0.6% of the time.

| Mode | Hit@1 (95% CI) | Hit@5 | MRR | Hit@1 German |
|---|---|---|---|---|
| BM25 | 0.68 (0.51 to 0.81) | 0.78 | 0.73 | 0.00 |
| **Dense (e5-large)** | **0.89** (0.78 to 0.97) | **1.00** | **0.94** | 0.80 |
| Hybrid (BM25 + dense, rank fusion) | 0.81 (0.68 to 0.92) | 0.95 | 0.88 | 0.40 |
| Hybrid + cross-encoder rerank | 0.78 (0.65 to 0.92) | 0.95 | 0.85 | 0.00 |

**Plain dense retrieval won, so it is the default.** BM25 cannot match German questions to English law text, which drags the fusion down, and the cross-encoder used here is English-only. An earlier version of this README reported "Hit@1 95%" for a reranker; that evaluation gave each question only 3 candidates (one right, two unrelated), so random chance was already 33%. It has been replaced by the harder test above.

**Chunking and config search (`docs/chunking_eval.md`).** Seven chunking strategies (whole article, word windows of 60/120/250/400, semantic sentence splitting) times four retrieval modes were searched, selecting on half the questions and scoring on the other half. Dense retrieval beat BM25 at every chunk size; chunk size and semantic splitting made no reliable difference (18 test questions, intervals about +/-0.2), and the dev-selected configuration did not beat the shipped default on the held-out half, so the default stays. This absorbs the retrieval-strategy and chunking benchmark of the former RAGForge repo, with a held-out split instead of selecting and reporting on the same questions.

### Gap analysis (`docs/gap_eval.md`)

Synthetic company documents with known ground truth, in German and English, including hard distractors such as "we have not appointed a DPO yet". Thresholds were tuned on a dev split and the table is the unseen test split (568 obligation/document pairs, 54% truly evidenced).

| Scorer | Precision of "found" | Recall of "found" | Recall of found + review | Unmet items sent to review |
|---|---|---|---|---|
| Dense embeddings (default) | 0.95 | 0.44 | 0.78 | 0.15 |
| Keyword rules (fallback, no model) | 1.00 | 0.46 | 0.46 | 0.00 |

What this means in practice:

- **When it says "found", it is usually right** (95% precision with embeddings). That is the property to trust, because a false "found" is false assurance.
- **Coverage is partial:** on unseen wordings it recovers 78% of evidenced obligations (found plus review). So **"gap" means "no evidence found", not "proven absent"** and needs a human check.
- **These documents are synthetic and written by the author**, so the numbers measure these paraphrases, not real company policies. They are an engineering check, not a claim about accuracy on real SMEs.
- Things that did not work are recorded in the report: a German-only query (English text scored lower regardless of meaning), a threshold-tuning bug, and a small zero-shot LLM verifier that was worse than plain similarity.

On the included example policy (`sample-data/company-docs/example_datenschutzrichtlinie.txt`, hand-written) the analysis finds the DPO, processing agreements and 72-hour breach process, flags records of processing, deletion, consent, NIS2 reporting, transfer safeguards for the US vendors and chatbot oversight as open, and sends the security measures to review: 9 of 10 as intended, one conservative. That is one document, shown as a demo.

## Known limitations

- **Ten obligations only** (GDPR Art. 7, 17, 28, 30, 33, 37, 46; NIS2 Art. 21, 23; AI Act Art. 14). It is not a full compliance audit and is not legal advice.
- **GDPR/BDSG text is not in the retrieval corpus** (only three paraphrased sample sentences exist), so GDPR obligations are cited by article number. The corpus covers the AI Act, NIS2 and CSRD.
- **Vendor and data-flow detection is a lexicon of 15 vendors**, not general extraction.
- **Default Docker image has no embedding model**, so analysis falls back to the keyword scorer (lower recall). Install `pip install .[ml]` for the dense scorer. Thresholds are tuned for `multilingual-e5-large`; changing `EMBEDDING_MODEL` means re-tuning them.
- **Stub endpoints:** `/simulate-dsar` returns a placeholder and searches no data; `/generate-policy` fills a fixed template. Both say so in their output.
- **Development mode is the default** (`ENV=development`): requests without a token act as the `demo-sme` tenant. Set `ENV=production` before exposing the API.
- **The dashboard** still shows the report as before; the new fields (`method`, `not_applicable`, `data_flows`) are returned by the API but not rendered yet.
- `/ask` with a Groq key is tested against a mocked HTTP transport only; its answer quality has not been evaluated.

## Run it

```bash
cp backend/.env.example backend/.env && cp frontend/.env.example frontend/.env.local
docker compose up --build
# Frontend: localhost:3000 · Backend: localhost:8000/docs
```

Demo login: tenant `demo-sme`, password `demo1234`. Three RBAC roles (owner/auditor/viewer): seed all three with `python backend/scripts/seed_demo_tenants.py`.

```bash
cd backend && pip install .[ml]
pytest -q                          # 57 tests, no model download needed
python eval/eval_retrieval.py      # writes docs/retrieval_eval.md
python eval/eval_chunking.py       # writes docs/chunking_eval.md (28-configuration grid, dev/test split)
python eval/eval_gap_analysis.py   # writes docs/gap_eval.md
```

Full deployment configs, RBAC details and migrations in [`docs/DETAILS.md`](docs/DETAILS.md). The regulation text comes from EUR-Lex (CELEX 32024R1689, 32022L2555, 32022L2464); source URLs are inside `backend/app/data/regulations/*.json`.
