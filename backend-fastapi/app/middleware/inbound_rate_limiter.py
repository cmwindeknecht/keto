import asyncio
import logging
import time
from collections import deque
from http import HTTPStatus

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


class InboundRateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Middleware to limit the rate of incoming requests.

    This implementation uses a simple token bucket algorithm to allow a certain
    number of requests per time window. It is designed to be used in a single
    instance of the application and is not distributed. For production use, consider
    using a distributed rate limiter like Redis or a third-party service.
    """

    ROUND_TO = 2

    def __init__(self, app, requests_limit: int = 5, requests_interval: float = 1.0, cleanup_interval: float = 30.0):
        super().__init__(app)
        self.requests_limit = requests_limit
        self.requests_interval = requests_interval
        self.clients: dict[str, deque] = {}
        self.cleanup_interval = cleanup_interval
        self.lock = asyncio.Lock()
        self.cleanup_loop = asyncio.ensure_future(self._cleanup_loop())

    async def _cleanup_loop(self):
        while True:
            await asyncio.sleep(self.cleanup_interval)
            await self._cleanup_stale_clients()

    async def _cleanup_stale_clients(self):
        async with self.lock:
            now = time.time()
            stale_clients = []
            for ip, calls in self.clients.items():
                if len(calls) == 0 or self._should_remove(calls[-1], now):
                    stale_clients.append(ip)

            logger.debug(f"Cleaning up {len(stale_clients)} stale clients")
            for ip in stale_clients:
                del self.clients[ip]

    async def dispatch(self, request: Request, call_next) -> JSONResponse:
        client_ip = request.client.host

        async with self.lock:
            now = time.time()

            if self.clients.get(client_ip, None) is None:
                self.clients[client_ip] = deque()

            # Remove timestamps that are outside the time window
            requests_deque = self.clients[client_ip]
            while len(requests_deque) > 0 and self._should_remove(requests_deque[0], now):
                requests_deque.popleft()

            # Reject the request if the number of requests in the current window exceeds the limit
            if len(requests_deque) >= self.requests_limit:
                retry_after = self.requests_interval - (now - requests_deque[0])
                return JSONResponse(
                    status_code=HTTPStatus.TOO_MANY_REQUESTS,
                    content={"error": "Rate limit exceeded", "retry_after": round(retry_after, self.ROUND_TO)},
                    headers={"Retry-After": str(round(retry_after, self.ROUND_TO))},
                )

            logger.debug(f"Recording request from {client_ip} at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))}")
            requests_deque.append(now)

        response = await call_next(request)
        return response

    def _should_remove(self, timestamp: float, now: float) -> bool:
        return timestamp <= now - self.requests_interval
