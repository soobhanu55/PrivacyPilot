from __future__ import annotations

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import AuditLogRecord, ComplianceReportRecord, UploadedDocument


class PersistenceService:
    async def save_uploaded_document(
        self, session: AsyncSession, tenant_key: str, document_id: str, filename: str, storage_path: str
    ) -> None:
        session.add(
            UploadedDocument(
                tenant_key=tenant_key,
                document_id=document_id,
                filename=filename,
                storage_path=storage_path,
            )
        )
        await session.commit()

    async def save_report(self, session: AsyncSession, tenant_key: str, report_payload: dict) -> None:
        session.add(
            ComplianceReportRecord(
                tenant_key=tenant_key,
                company_id=report_payload["company_id"],
                compliance_score=report_payload["compliance_score"],
                report_payload=report_payload,
            )
        )
        await session.commit()

    async def latest_report(self, session: AsyncSession, tenant_key: str) -> dict | None:
        stmt = (
            select(ComplianceReportRecord)
            .where(ComplianceReportRecord.tenant_key == tenant_key)
            .order_by(desc(ComplianceReportRecord.created_at))
            .limit(1)
        )
        row = (await session.execute(stmt)).scalar_one_or_none()
        return row.report_payload if row else None

    async def save_audit_entries(self, session: AsyncSession, tenant_key: str, entries: list[dict]) -> None:
        for entry in entries:
            session.add(
                AuditLogRecord(
                    tenant_key=tenant_key,
                    workflow_id=entry["workflow_id"],
                    agent=entry["agent"],
                    input_summary=entry["input_summary"],
                    output_summary=entry["output_summary"],
                    model=entry["model"],
                    trace=entry["trace"],
                )
            )
        await session.commit()

    async def list_audit_entries(self, session: AsyncSession, tenant_key: str, limit: int = 200) -> list[dict]:
        stmt = (
            select(AuditLogRecord)
            .where(AuditLogRecord.tenant_key == tenant_key)
            .order_by(desc(AuditLogRecord.created_at))
            .limit(limit)
        )
        rows = (await session.execute(stmt)).scalars().all()
        return [
            {
                "timestamp": row.created_at,
                "workflow_id": row.workflow_id,
                "agent": row.agent,
                "input_summary": row.input_summary,
                "output_summary": row.output_summary,
                "model": row.model,
                "trace": row.trace,
            }
            for row in rows
        ]


persistence_service = PersistenceService()
