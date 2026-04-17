from __future__ import annotations

from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import get_settings

# pbkdf2_sha256 is stable across platforms and avoids bcrypt backend issues.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
settings = get_settings()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(subject: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {"sub": subject, "exp": expires, "typ": "access"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(subject: str) -> str:
    expires = datetime.now(timezone.utc) + timedelta(days=14)
    payload = {"sub": subject, "exp": expires, "typ": "refresh"}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise ValueError("Invalid token") from exc


def decode_access_token(token: str) -> str:
    payload = decode_token(token)
    if payload.get("typ") != "access":
        raise ValueError("Invalid token type")
    subject = payload.get("sub")
    if not subject:
        raise ValueError("Token subject missing")
    return str(subject)


def decode_refresh_token(token: str) -> str:
    payload = decode_token(token)
    if payload.get("typ") != "refresh":
        raise ValueError("Invalid token type")
    subject = payload.get("sub")
    if not subject:
        raise ValueError("Token subject missing")
    return str(subject)
