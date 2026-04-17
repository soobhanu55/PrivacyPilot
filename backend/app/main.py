from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.api.routes import router
from app.core.config import get_settings
from app.core.logging import configure_logging, log_request_middleware
from app.core.security import hash_password
from app.db.models import Base, Tenant
from app.db.session import SessionLocal, engine

settings = get_settings()


@asynccontextmanager
async def lifespan(_app: FastAPI):
    configure_logging()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with SessionLocal() as session:
        tenant = (await session.execute(select(Tenant).where(Tenant.tenant_key == "demo-sme"))).scalar_one_or_none()
        if not tenant:
            session.add(
                Tenant(
                    tenant_key="demo-sme",
                    display_name="Demo German SME",
                    hashed_password=hash_password("demo1234"),
                    role="owner",
                )
            )
            await session.commit()
    yield


app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
app.middleware("http")(log_request_middleware)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
