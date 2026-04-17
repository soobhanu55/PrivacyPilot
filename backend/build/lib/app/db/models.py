from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_key: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UploadedDocument(Base):
    __tablename__ = "uploaded_documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    tenant_key: Mapped[str] = mapped_column(String(120), index=True)
    filename: Mapped[str] = mapped_column(String(500))
    storage_path: Mapped[str] = mapped_column(String(1000))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ComplianceReportRecord(Base):
    __tablename__ = "compliance_reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_key: Mapped[str] = mapped_column(String(120), index=True)
    company_id: Mapped[str] = mapped_column(String(120), index=True)
    compliance_score: Mapped[int] = mapped_column(Integer)
    report_payload: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLogRecord(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_key: Mapped[str] = mapped_column(String(120), index=True)
    workflow_id: Mapped[str] = mapped_column(String(120), index=True)
    agent: Mapped[str] = mapped_column(String(120))
    input_summary: Mapped[str] = mapped_column(Text)
    output_summary: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(120))
    trace: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
