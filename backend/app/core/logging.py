from __future__ import annotations

import logging
from time import perf_counter
from uuid import uuid4

from fastapi import Request


def configure_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s request_id=%(request_id)s %(message)s",
    )


class RequestLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.setdefault("extra", {})
        extra.setdefault("request_id", self.extra.get("request_id", "-"))
        return msg, kwargs


async def log_request_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", str(uuid4()))
    start = perf_counter()
    logger = RequestLoggerAdapter(logging.getLogger("dsgvo.api"), {"request_id": request_id})
    response = await call_next(request)
    duration_ms = int((perf_counter() - start) * 1000)
    logger.info("%s %s status=%s duration_ms=%s", request.method, request.url.path, response.status_code, duration_ms)
    response.headers["x-request-id"] = request_id
    return response
