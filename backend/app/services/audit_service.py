from __future__ import annotations

from collections import deque

from app.models.schemas import AuditLogEntry


class AuditService:
    def __init__(self) -> None:
        self._entries: deque[AuditLogEntry] = deque(maxlen=10000)

    def log(self, entry: AuditLogEntry) -> None:
        self._entries.appendleft(entry)

    def list_entries(self) -> list[AuditLogEntry]:
        return list(self._entries)


audit_service = AuditService()
