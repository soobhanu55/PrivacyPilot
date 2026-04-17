from __future__ import annotations

from celery import Celery

from app.core.config import get_settings
from app.services.compliance_service import compliance_service

settings = get_settings()
celery_app = Celery("dsgvo_worker", broker=settings.redis_url, backend=settings.redis_url)


@celery_app.task
def continuous_monitoring(company_id: str, document_ids: list[str]) -> dict:
    report = __import__("asyncio").run(compliance_service.analyze(company_id=company_id, document_ids=document_ids))
    return report.model_dump()
