"""initial tables

Revision ID: 20260414_0001
Revises:
Create Date: 2026-04-14
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "20260414_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("tenant_key", sa.String(length=120), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_tenants_tenant_key", "tenants", ["tenant_key"], unique=True)

    op.create_table(
        "uploaded_documents",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("document_id", sa.String(length=120), nullable=False),
        sa.Column("tenant_key", sa.String(length=120), nullable=False),
        sa.Column("filename", sa.String(length=500), nullable=False),
        sa.Column("storage_path", sa.String(length=1000), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_uploaded_documents_document_id", "uploaded_documents", ["document_id"], unique=True)
    op.create_index("ix_uploaded_documents_tenant_key", "uploaded_documents", ["tenant_key"], unique=False)

    op.create_table(
        "compliance_reports",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("tenant_key", sa.String(length=120), nullable=False),
        sa.Column("company_id", sa.String(length=120), nullable=False),
        sa.Column("compliance_score", sa.Integer(), nullable=False),
        sa.Column("report_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_compliance_reports_tenant_key", "compliance_reports", ["tenant_key"], unique=False)
    op.create_index("ix_compliance_reports_company_id", "compliance_reports", ["company_id"], unique=False)

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, primary_key=True),
        sa.Column("tenant_key", sa.String(length=120), nullable=False),
        sa.Column("workflow_id", sa.String(length=120), nullable=False),
        sa.Column("agent", sa.String(length=120), nullable=False),
        sa.Column("input_summary", sa.Text(), nullable=False),
        sa.Column("output_summary", sa.Text(), nullable=False),
        sa.Column("model", sa.String(length=120), nullable=False),
        sa.Column("trace", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_audit_logs_tenant_key", "audit_logs", ["tenant_key"], unique=False)
    op.create_index("ix_audit_logs_workflow_id", "audit_logs", ["workflow_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_audit_logs_workflow_id", table_name="audit_logs")
    op.drop_index("ix_audit_logs_tenant_key", table_name="audit_logs")
    op.drop_table("audit_logs")
    op.drop_index("ix_compliance_reports_company_id", table_name="compliance_reports")
    op.drop_index("ix_compliance_reports_tenant_key", table_name="compliance_reports")
    op.drop_table("compliance_reports")
    op.drop_index("ix_uploaded_documents_tenant_key", table_name="uploaded_documents")
    op.drop_index("ix_uploaded_documents_document_id", table_name="uploaded_documents")
    op.drop_table("uploaded_documents")
    op.drop_index("ix_tenants_tenant_key", table_name="tenants")
    op.drop_table("tenants")
