# Architecture Overview

## Backend

- FastAPI async API layer
- LangGraph multi-agent orchestration
- Hybrid RAG retriever service
- Knowledge graph engine with NetworkX
- Celery worker for continuous monitoring jobs
- Audit logging service for explainable traces

## Frontend

- Next.js dashboard with dedicated pages:
  - Upload Center
  - Compliance Score Dashboard
  - Risk Heatmap
  - Document Insights
  - Audit Logs

## Data and AI

- Legal corpus support for DSGVO, BDSG, EU AI Act
- Company document ingestion and chunking
- Risk scoring and recommendation generation
- Source-linked outputs and traceability

## Deployment

- Dockerized backend, worker, frontend
- Redis and Qdrant infrastructure services
- GitHub Actions CI for backend and frontend builds
- Ready for EU-region deployment (AWS/GCP/Hetzner)
