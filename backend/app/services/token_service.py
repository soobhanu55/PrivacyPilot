from __future__ import annotations

import hashlib
from datetime import UTC, datetime

import redis

from app.core.config import get_settings
from app.core.security import decode_token

class TokenService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._redis: redis.Redis | None = None
        self._revoked_tokens: set[str] = set()

    def _client(self) -> redis.Redis:
        if self._redis is None:
            self._redis = redis.Redis.from_url(self._settings.redis_url, decode_responses=True)
        return self._redis

    def _key(self, token: str) -> str:
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return f"{self._settings.token_revoke_prefix}{digest}"

    def revoke(self, token: str) -> None:
        key = self._key(token)
        try:
            payload = decode_token(token)
            exp = int(payload.get("exp", 0))
            now = int(datetime.now(UTC).timestamp())
            ttl = max(1, exp - now)
            self._client().setex(key, ttl, "1")
            return
        except Exception:
            # Fall back to in-memory revocation if Redis or token parsing fails.
            pass
        self._revoked_tokens.add(token)

    def is_revoked(self, token: str) -> bool:
        key = self._key(token)
        try:
            return bool(self._client().get(key))
        except Exception:
            pass
        return token in self._revoked_tokens


token_service = TokenService()
