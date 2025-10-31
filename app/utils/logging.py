# app/utils/logging.py
import uuid
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("orcha")
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s %(levelname)s [%(trace_id)s] %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

def get_trace_id():
    return str(uuid.uuid4())

class TraceIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        trace_id = request.headers.get("x-trace-id") or get_trace_id()
        request.state.trace_id = trace_id
        # inject into logging record via extra injection
        extra = {"trace_id": trace_id}
        # monkeypatch logger.makeRecord to include trace_id? simpler: use adapter
        adapter = logging.LoggerAdapter(logger, extra)
        request.state.logger = adapter
        adapter.info(f"start {request.method} {request.url.path}")
        response = await call_next(request)
        adapter.info(f"end {request.method} {request.url.path} -> {response.status_code}")
        return response
