from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import authenticate_tenant, get_current_tenant
from app.core.security import create_access_token
from app.db.session import get_db_session
from app.models.schemas import AnalyzeRequest, LoginRequest, PolicyRequest, TokenResponse
from app.services.audit_service import audit_service
from app.services.compliance_service import compliance_service
from app.services.persistence_service import persistence_service

router = APIRouter()
UPLOAD_DIR = Path("sample-data/company-docs/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.post("/auth/login", response_model=TokenResponse)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_db_session)) -> TokenResponse:
    valid = await authenticate_tenant(session, payload.tenant_key, payload.password)
    if not valid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return TokenResponse(access_token=create_access_token(payload.tenant_key))


@router.post("/upload-documents")
async def upload_documents(
    files: list[UploadFile] = File(...),
    tenant_key: str = Depends(get_current_tenant),
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
    tenant_key: str = Depends(get_current_tenant), session: AsyncSession = Depends(get_db_session)
):
    report = await persistence_service.latest_report(session, tenant_key=tenant_key)
    if report:
        return {"report": report}
    fallback = await compliance_service.latest_report()
    return {"report": fallback.model_dump() if fallback else None}


@router.post("/generate-policy")
async def generate_policy(payload: PolicyRequest, tenant_key: str = Depends(get_current_tenant)):
    return await compliance_service.generate_policy(payload)


@router.get("/audit-log")
async def audit_log(tenant_key: str = Depends(get_current_tenant), session: AsyncSession = Depends(get_db_session)):
    entries = await persistence_service.list_audit_entries(session, tenant_key=tenant_key)
    return {"entries": entries}


@router.post("/simulate-dsar/{subject_id}")
async def simulate_dsar(subject_id: str, tenant_key: str = Depends(get_current_tenant)):
    return await compliance_service.simulate_dsar(subject_id)


@router.get("/knowledge-graph")
async def knowledge_graph(tenant_key: str = Depends(get_current_tenant)):
    return await compliance_service.graph_payload()
