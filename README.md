# PrivacyPilot

Production-grade compliance SaaS for German SMEs — continuous DSGVO (GDPR), BDSG, EU AI Act, and NIS2 monitoring, with a hybrid RAG stack, a knowledge graph, and multi-tenant RBAC.

![Reranker evaluation, terminal recording](docs/demo.gif)

## Results

```
Reranker (cross-encoder, 20-question GDPR eval set): Hit@1 = 19/20 (95.0%)
```
The one miss is kept in the eval set: "third country data transfer safeguards" ranked an HR-unrelated sentence above the correct SCC clause.

**Known gap, stated plainly:** the risk-classification agent currently returns 3 hardcoded findings regardless of input, despite being logged as `hybrid-rules+llm`. Not a real classifier yet — no score reported because nothing is actually being measured. This is the next real piece of work, not something already done.

## Stack

FastAPI backend · Next.js frontend · LangGraph multi-agent workflow · hybrid RAG (dense + BM25 + cross-encoder reranking) · knowledge graph for data flows · PostgreSQL/Alembic · Redis · Docker

## Run it

```bash
cp backend/.env.example backend/.env && cp frontend/.env.example frontend/.env.local
docker compose up --build
# Frontend: localhost:3000 · Backend: localhost:8000/docs
```

Demo login: tenant `demo-sme`, password `demo1234`. Three RBAC roles (owner/auditor/viewer) — seed all three with `python backend/scripts/seed_demo_tenants.py`.

Full deployment configs, RBAC details, and DB migration steps in [`docs/DETAILS.md`](docs/DETAILS.md).
