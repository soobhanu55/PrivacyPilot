# PrivacyPilot — Full Details

Production-grade SaaS platform for continuous compliance with DSGVO (GDPR), BDSG, EU AI Act, and NIS2.

## Platform Capabilities

- Document analysis workflow (LangGraph): read uploads, detect vendors, match 10 GDPR / NIS2 / AI Act obligations to evidence passages, score, cite articles
- Regulation question answering over the AI Act, NIS2 and CSRD (dense retrieval; optional Groq-generated answer)
- Knowledge graph built from the actual findings: company, vendors (flagged if outside the EU/EEA), obligations and the documents that evidence them
- Audit log of every workflow step, with the scoring method recorded
- Multi-tenant JWT auth with RBAC, per-tenant documents, reports and graphs
- FastAPI backend, Next.js dashboard, Celery/Redis workers, PostgreSQL/Alembic

## Analysis Pipeline

1. `document_ingestion_agent` reads each uploaded file (TXT, Markdown, PDF, DOCX) and splits it into passages. Unreadable files are recorded and skipped.
2. `data_flow_mapping_agent` finds vendors from a lexicon of 15 and flags those headquartered outside the EU/EEA.
3. `risk_classification_agent` matches each obligation (`app/services/gap_analysis.py`) to its best evidence passage with a scorer: dense multilingual-e5 similarity when the `ml` extra is installed, keyword rules otherwise. Obligations whose topic never appears (no third-country vendor, no AI system) are marked not applicable.
4. `recommendation_agent` computes a severity-weighted score (found = 1, review = 0.5, gap = 0) and the German summary.
5. `audit_trail_agent` closes the audit trace.

Only the tenant's own uploads are readable by `/analyze-compliance`; document ids that belong to someone else are reported as unknown. Reports and graphs are held per tenant.

## Monorepo Structure

- `backend` - FastAPI APIs, AI agents, RAG, graph engine, workers
- `frontend` - Next.js dashboard and analyst workflows
- `infra` - Docker, deployment and environment templates
- `sample-data` - Demo documents and legal corpus snippets
- `docs` - Architecture and operations documentation

## Deployment Ready

- Managed compose (Supabase/Qdrant + server workers): `infra/docker-compose.managed.yml`
- Production compose: `infra/docker-compose.prod.yml`
- TLS reverse proxy overlay: `infra/docker-compose.tls.yml`
- Caddy config: `infra/Caddyfile`
- Build/publish/deploy workflow: `.github/workflows/deploy.yml`
- Vercel frontend deploy workflow: `.github/workflows/deploy-vercel.yml`
- Deployment runbook: `docs/deployment.md`
- Production env templates:
  - `backend/.env.production.example`
  - `frontend/.env.production.example`

## Quick Start

1. Copy env templates:
   - `backend/.env.example` to `backend/.env`
   - `frontend/.env.example` to `frontend/.env.local`
2. Start stack:
   - `docker compose up --build`
3. Open:
   - Frontend: `http://localhost:3000`
   - Backend: `http://localhost:8000/docs`

## Demo Authentication

- Default tenant: `demo-sme`
- Password: `demo1234`
- Login endpoint: `POST /auth/login`
- Tenant onboarding: `POST /auth/register`
- Refresh token: `POST /auth/refresh`
- Logout: `POST /auth/logout`

## RBAC Roles

- `owner`: full access including upload, analyze, policy, DSAR, audit, graph
- `auditor`: compliance operations and audit/graph visibility
- `viewer`: read-only visibility for report, audit logs, graph
- Current identity endpoint: `GET /auth/me`
- Owner role management endpoint: `PATCH /admin/tenants/{tenant_key}/role`

In development mode, API routes also allow fallback tenant access for local dashboard UX.

## Database Migrations

- Migration config: `backend/alembic.ini`
- Initial migration: `backend/alembic/versions/20260414_0001_initial_tables.py`
- Role migration: `backend/alembic/versions/20260414_0002_tenant_role.py`
- Run migrations:
  - `cd backend`
  - `alembic upgrade head`

## Token Revocation

- Logout revokes bearer tokens via Redis-backed revocation keys.
- If Redis is unavailable, the service falls back to in-memory revocation.

## End-to-End Smoke Run

- Start services: `docker compose up --build`
- Run smoke script:
  - `cd backend`
  - `python scripts/e2e_smoke.py`

## Demo Tenant Seed

- Seed owner/auditor/viewer tenants:
  - `cd backend`
  - `python scripts/seed_demo_tenants.py`
- Credentials:
  - `demo-owner` / `owner1234`
  - `demo-auditor` / `auditor1234`
  - `demo-viewer` / `viewer1234`

## Dedicated ML Worker

- `ml-worker` runs queue-isolated ML tasks with optional dependencies.
- API queue routing:
  - Default queue (standard worker): compliance/background jobs
  - `ml` queue (`ml-worker`): reranking/inference jobs
- ML endpoints:
  - `POST /ml/rerank` -> enqueue rerank job
  - `GET /ml/tasks/{task_id}` -> poll status/result

## Evaluation

Full reports: [`retrieval_eval.md`](retrieval_eval.md) and [`gap_eval.md`](gap_eval.md). Reproduce from `backend/` with `pip install .[ml]`, then `python eval/eval_retrieval.py` and `python eval/eval_gap_analysis.py`.

- **Retrieval** (37 hand-labelled questions, 178 articles, article-level): BM25 Hit@1 0.68, **dense e5-large 0.89 (Hit@5 1.00, MRR 0.94)**, BM25 + dense fusion 0.81, fusion + English cross-encoder 0.78. German questions: BM25 0.00, dense 0.80. Dense is the default. The earlier 20-question reranker eval (95% Hit@1) gave each question 3 candidates, two of them unrelated, so chance was 33%; it was removed.
- **Gap analysis** (60 dev / 60 test synthetic documents, German and English, with hard distractors): dense scorer, unseen test split, precision of "found" 0.95, recall of found + review 0.78, 15% of unmet items routed to review. Keyword fallback: precision 1.00, recall 0.46. The documents are synthetic and written by the author, so this is an engineering check, not an accuracy claim for real policies. "Gap" means "no evidence found".
- **Previously documented gap, now closed:** the risk-classification agent used to return three hardcoded findings for any input, the ingestion agent invented "facts" without reading documents, and the retriever was not called by anything. Those have been replaced by the pipeline above, and `tests/test_workflow.py` now asserts that the report changes with the document content.

## Optional ML Dependencies

- Core backend images skip heavyweight local embedding stacks for faster builds; in that image analysis uses the keyword scorer.
- For the dense scorer and the Q&A retriever's embeddings: `cd backend && pip install .[ml]`. Thresholds are tuned for `intfloat/multilingual-e5-large`; if you change `EMBEDDING_MODEL`, re-run `eval/eval_gap_analysis.py` and update `DenseScorer.thresholds`.
- `GROQ_API_KEY` (optional, environment only) enables generated answers in `POST /ask`.

## Stub endpoints

- `POST /simulate-dsar/{id}` returns a placeholder and searches no data store.
- `POST /generate-policy` fills a fixed template and says so (`note_de`).

## Demo Scenario

Run the included demo script to simulate:

- Upload HR + Marketing documents
- Detect violations (consent tracking, retention, transfer risk)
- Generate risk report and policy artifacts
- Compare compliance score before/after recommendations

See `sample-data/demo-script.md` for step-by-step flow.
