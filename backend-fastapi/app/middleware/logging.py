"""Request/response logging middleware."""

import json
import logging
import time
from typing import Callable
from uuid import uuid4

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import Message


logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response with unique request ID."""
        request_id = str(uuid4())

        # Cache request body for multiple reads
        receive_ = await request._receive()
        async def receive() -> Message:
            return receive_
        request._receive = receive

        # Execute request and time it
        start_time = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception as e:
            logger.exception({"request_id": request_id, "path": request.url.path, "error": str(e)})
            raise

        execution_time = time.perf_counter() - start_time
        response.headers["X-API-Request-ID"] = request_id

        # Capture response body
        resp_body_chunks = []
        async for chunk in response.__dict__.get("body_iterator", []):
            resp_body_chunks.append(chunk)
        response_body = b"".join(resp_body_chunks)

        # Build log data
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path + (f"?{request.query_params}" if request.query_params else ""),
            "status": response.status_code,
            "request_time": f"{execution_time:.4f}s",
        }

        # Try to add request body
        try:
            log_data["request_body"] = await request.json()
        except Exception:
            logger.warning(f"Failed to parse request body for logging on request {request_id}")

        # Try to add response body
        try:
            log_data["response_body"] = json.loads(response_body.decode())
        except Exception:
            log_data["response_body"] = response_body.decode() if response_body else None

        logger.info(json.dumps(log_data))

        # Return response with captured body
        return Response(
            content=response_body,
            status_code=response.status_code,
            headers=dict(response.headers),
        )
