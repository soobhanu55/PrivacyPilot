# DSGVO Copilot - AI Compliance Agent for German SMEs

Production-grade SaaS platform for continuous compliance with DSGVO (GDPR), BDSG, EU AI Act, and NIS2.

## Platform Capabilities

- Multi-agent compliance analysis workflow with LangGraph
- Hybrid RAG stack (dense + BM25 + cross-encoder reranking)
- Knowledge graph for data flows and legal obligations
- Continuous monitoring with background workers
- Audit-ready decision logs with explainability in German
- FastAPI backend and Next.js frontend dashboard

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

## Optional ML Dependencies

- Core backend images skip heavyweight local embedding stacks for faster builds.
- To enable local cross-encoder/embedding experiments outside Docker:
  - `cd backend`
  - `pip install .[ml]`

## Dedicated ML Worker

- `ml-worker` runs queue-isolated ML tasks with optional dependencies.
- API queue routing:
  - Default queue (standard worker): compliance/background jobs
  - `ml` queue (`ml-worker`): reranking/inference jobs
- ML endpoints:
  - `POST /ml/rerank` -> enqueue rerank job
  - `GET /ml/tasks/{task_id}` -> poll status/result

## Demo Scenario

Run the included demo script to simulate:

- Upload HR + Marketing documents
- Detect violations (consent tracking, retention, transfer risk)
- Generate risk report and policy artifacts
- Compare compliance score before/after recommendations

See `sample-data/demo-script.md` for step-by-step flow.
