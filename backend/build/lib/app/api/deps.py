from __future__ import annotations

from app.core.config import get_settings
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_access_token, verify_password
from app.db.models import Tenant
from app.db.session import get_db_session

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)
settings = get_settings()


async def get_current_tenant(
    token: str | None = Depends(oauth2_scheme), session: AsyncSession = Depends(get_db_session)
) -> str:
    if not token and settings.env == "development":
        return "demo-sme"
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing token")
    try:
        tenant_key = decode_access_token(token)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc
    stmt = select(Tenant).where(Tenant.tenant_key == tenant_key)
    tenant = (await session.execute(stmt)).scalar_one_or_none()
    if not tenant:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unknown tenant")
    return tenant_key


async def authenticate_tenant(session: AsyncSession, tenant_key: str, password: str) -> bool:
    stmt = select(Tenant).where(Tenant.tenant_key == tenant_key)
    tenant = (await session.execute(stmt)).scalar_one_or_none()
    if not tenant:
        return False
    return verify_password(password, tenant.hashed_password)
