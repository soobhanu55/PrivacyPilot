from __future__ import annotations

from celery import Celery

from app.core.config import get_settings
from app.services.compliance_service import compliance_service
from app.services.ml_service import rerank_candidates

settings = get_settings()
celery_app = Celery("dsgvo_worker", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_routes = {
    "app.worker.celery_app.continuous_monitoring": {"queue": "default"},
    "app.worker.celery_app.rerank_candidates_task": {"queue": "ml"},
}


@celery_app.task
def continuous_monitoring(company_id: str, document_ids: list[str]) -> dict:
    report = __import__("asyncio").run(compliance_service.analyze(company_id=company_id, document_ids=document_ids))
    return report.model_dump()


@celery_app.task(name="app.worker.celery_app.rerank_candidates_task")
def rerank_candidates_task(query: str, candidates: list[str], top_k: int = 3) -> dict:
    ranked = rerank_candidates(query=query, candidates=candidates, top_k=top_k)
    return {"query": query, "results": ranked}
