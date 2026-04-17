from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from sqlalchemy import select

# Ensure local backend package takes precedence over globally installed package.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password
from app.db.models import Tenant
from app.db.session import SessionLocal


SEED_TENANTS = [
    ("demo-owner", "Demo Owner GmbH", "owner1234", "owner"),
    ("demo-auditor", "Demo Auditor GmbH", "auditor1234", "auditor"),
    ("demo-viewer", "Demo Viewer GmbH", "viewer1234", "viewer"),
]


async def seed() -> None:
    async with SessionLocal() as session:
        for tenant_key, display_name, password, role in SEED_TENANTS:
            existing = (await session.execute(select(Tenant).where(Tenant.tenant_key == tenant_key))).scalar_one_or_none()
            if existing:
                existing.display_name = display_name
                existing.hashed_password = hash_password(password)
                existing.role = role
            else:
                session.add(
                    Tenant(
                        tenant_key=tenant_key,
                        display_name=display_name,
                        hashed_password=hash_password(password),
                        role=role,
                    )
                )
        await session.commit()
    print("Seeded demo tenants: demo-owner, demo-auditor, demo-viewer")


if __name__ == "__main__":
    asyncio.run(seed())
