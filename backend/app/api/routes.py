from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Header, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import authenticate_tenant, get_current_tenant, get_current_tenant_role, require_roles
from app.core.security import create_access_token, create_refresh_token, decode_refresh_token, hash_password
from app.db.models import Tenant
from app.db.session import get_db_session
from app.models.schemas import (
    AnalyzeRequest,
    LoginRequest,
    MLRerankRequest,
    PolicyRequest,
    RefreshRequest,
    RegisterTenantRequest,
    RoleUpdateRequest,
    TokenResponse,
)
from app.services.audit_service import audit_service
from app.services.compliance_service import compliance_service
from app.services.persistence_service import persistence_service
from app.services.token_service import token_service
from app.worker.celery_app import rerank_candidates_task

router = APIRouter()
UPLOAD_DIR = Path("sample-data/company-docs/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/auth/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_db_session)) -> TokenResponse:
    valid = await authenticate_tenant(session, payload.tenant_key, payload.password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    tenant = (await session.execute(select(Tenant).where(Tenant.tenant_key == payload.tenant_key))).scalar_one()
    return TokenResponse(
        access_token=create_access_token(tenant.tenant_key),
        refresh_token=create_refresh_token(tenant.tenant_key),
    )


@router.post("/auth/register")
async def register_tenant(payload: RegisterTenantRequest, session: AsyncSession = Depends(get_db_session)):
    existing = (await session.execute(select(Tenant).where(Tenant.tenant_key == payload.tenant_key))).scalar_one_or_none()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Tenant key already exists")
    tenant = Tenant(
        tenant_key=payload.tenant_key,
        display_name=payload.display_name,
        hashed_password=hash_password(payload.password),
        role=payload.role,
    )
    session.add(tenant)
    await session.commit()
    return {"tenant_key": payload.tenant_key, "display_name": payload.display_name}


@router.post("/auth/refresh", response_model=TokenResponse)
async def refresh_token(payload: RefreshRequest) -> TokenResponse:
    try:
        subject = decode_refresh_token(payload.refresh_token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token") from exc
    if token_service.is_revoked(payload.refresh_token):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token revoked")
    return TokenResponse(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


@router.post("/auth/logout")
async def logout(authorization: str | None = Header(default=None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    token_service.revoke(token)
    return {"status": "logged_out"}


@router.get("/auth/me")
async def auth_me(
    tenant_key: str = Depends(get_current_tenant),
    role: str = Depends(get_current_tenant_role),
):
    return {"tenant_key": tenant_key, "role": role}


@router.patch("/admin/tenants/{target_tenant_key}/role")
async def update_tenant_role(
    target_tenant_key: str,
    payload: RoleUpdateRequest,
    _: None = Depends(require_roles("owner")),
    session: AsyncSession = Depends(get_db_session),
):
    target = (await session.execute(select(Tenant).where(Tenant.tenant_key == target_tenant_key))).scalar_one_or_none()
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant not found")
    target.role = payload.role
    await session.commit()
    return {"tenant_key": target.tenant_key, "role": target.role}


@router.get("/admin/tenants")
async def list_tenants(
    _: None = Depends(require_roles("owner")),
    session: AsyncSession = Depends(get_db_session),
):
    rows = (await session.execute(select(Tenant).order_by(Tenant.tenant_key.asc()))).scalars().all()
    return {
        "tenants": [
            {"tenant_key": row.tenant_key, "display_name": row.display_name, "role": row.role}
            for row in rows
        ]
    }


@router.post("/upload-documents")
async def upload_documents(
    files: list[UploadFile] = File(...),
    tenant_key: str = Depends(get_current_tenant),
    _: None = Depends(require_roles("owner", "auditor")),
    session: AsyncSession = Depends(get_db_session),
) -> dict[str, list[dict[str, str]]]:
    uploaded = []
    for file in files:
        doc_id = str(uuid4())
        target = UPLOAD_DIR / f"{doc_id}-{file.filename}"
        content = await file.read()
        target.write_bytes(content)
        await persistence_service.save_uploaded_document(
            session=session, tenant_key=tenant_key, document_id=doc_id, filename=file.filename, storage_path=str(target)
        )
        uploaded.append({"document_id": doc_id, "filename": file.filename, "path": str(target)})
    return {"uploaded_documents": uploaded}


@router.post("/analyze-compliance")
async def analyze_compliance(
    payload: AnalyzeRequest,
    tenant_key: str = Depends(get_current_tenant),
    _: None = Depends(require_roles("owner", "auditor")),
    session: AsyncSession = Depends(get_db_session),
):
    report = await compliance_service.analyze(payload.company_id, payload.document_ids)
    await persistence_service.save_report(session, tenant_key=tenant_key, report_payload=report.model_dump(mode="json"))
    await persistence_service.save_audit_entries(
        session, tenant_key=tenant_key, entries=[entry.model_dump(mode="json") for entry in audit_service.list_entries()]
    )
    return report.model_dump()


@router.get("/risk-report")
async def risk_report(
    tenant_key: str = Depends(get_current_tenant),
    _: None = Depends(require_roles("owner", "auditor", "viewer")),
    session: AsyncSession = Depends(get_db_session),
):
    report = await persistence_service.latest_report(session, tenant_key=tenant_key)
    if report:
        return {"report": report}
    fallback = await compliance_service.latest_report()
    return {"report": fallback.model_dump() if fallback else None}


@router.post("/generate-policy")
async def generate_policy(
    payload: PolicyRequest,
    tenant_key: str = Depends(get_current_tenant),
    _: None = Depends(require_roles("owner", "auditor")),
):
    return await compliance_service.generate_policy(payload)


@router.get("/audit-log")
async def audit_log(
    tenant_key: str = Depends(get_current_tenant),
    _: None = Depends(require_roles("owner", "auditor", "viewer")),
    session: AsyncSession = Depends(get_db_session),
):
    entries = await persistence_service.list_audit_entries(session, tenant_key=tenant_key)
    return {"entries": entries}


@router.post("/simulate-dsar/{subject_id}")
async def simulate_dsar(
    subject_id: str,
    tenant_key: str = Depends(get_current_tenant),
    _: None = Depends(require_roles("owner", "auditor")),
):
    return await compliance_service.simulate_dsar(subject_id)


@router.get("/knowledge-graph")
async def knowledge_graph(
    tenant_key: str = Depends(get_current_tenant),
    _: None = Depends(require_roles("owner", "auditor", "viewer")),
):
    return await compliance_service.graph_payload()


@router.post("/ml/rerank")
async def ml_rerank(
    payload: MLRerankRequest,
    _: None = Depends(require_roles("owner", "auditor")),
):
    task = rerank_candidates_task.delay(payload.query, payload.candidates, payload.top_k)
    return {"task_id": task.id, "status": "queued", "queue": "ml"}


@router.get("/ml/tasks/{task_id}")
async def ml_task_status(task_id: str, _: None = Depends(require_roles("owner", "auditor", "viewer"))):
    result = rerank_candidates_task.AsyncResult(task_id)
    if not result.ready():
        return {"task_id": task_id, "status": result.status}
    return {"task_id": task_id, "status": result.status, "result": result.result}
