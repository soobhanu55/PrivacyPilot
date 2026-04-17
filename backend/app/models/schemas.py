from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


RiskLevel = Literal["Low", "Medium", "High"]
TenantRole = Literal["owner", "auditor", "viewer"]


class DocumentChunk(BaseModel):
    document_id: str
    chunk_id: str
    text: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class RiskItem(BaseModel):
    id: str
    title: str
    regulation: str
    severity: RiskLevel
    explanation_de: str
    recommendation_de: str
    source_refs: list[str] = Field(default_factory=list)


class ComplianceReport(BaseModel):
    company_id: str
    compliance_score: int = Field(ge=0, le=100)
    summary_de: str
    risks: list[RiskItem]
    generated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    next_actions_de: list[str] = Field(default_factory=list)


class AuditLogEntry(BaseModel):
    timestamp: datetime = Field(default_factory=lambda: datetime.now(UTC))
    workflow_id: str
    agent: str
    input_summary: str
    output_summary: str
    model: str
    trace: dict[str, Any] = Field(default_factory=dict)


class AnalyzeRequest(BaseModel):
    company_id: str
    document_ids: list[str]
    departments: list[str] = Field(default_factory=list)


class PolicyRequest(BaseModel):
    company_id: str
    policy_type: Literal["privacy_policy", "dpa"]
    context: str


class LoginRequest(BaseModel):
    tenant_key: str
    password: str


class RegisterTenantRequest(BaseModel):
    tenant_key: str
    display_name: str
    password: str
    role: TenantRole = "owner"


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RoleUpdateRequest(BaseModel):
    role: TenantRole


class MLRerankRequest(BaseModel):
    query: str
    candidates: list[str]
    top_k: int = Field(default=3, ge=1, le=20)
