import asyncio
import functools
import inspect
import logging
import threading
import time
from collections import deque

from app.core.exceptions import USDAAPIRateLimitError

logger = logging.getLogger(__name__)


class OutboundRateLimiter:
    def __init__(self, max_requests: int = 1000, requests_interval: float = 3600.0):  # USDA API allows 1000 requests per hour
        self.max_requests = max_requests
        self.requests_interval = requests_interval
        self.calls = deque()
        self.lock = threading.Lock()
        self.asyncio_lock = asyncio.Lock()

    def __call__(self, func):
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                await self.validate_request_limit_async()
                return await func(*args, **kwargs)

            return async_wrapper

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            self.validate_request_limit()
            return func(*args, **kwargs)

        return sync_wrapper

    def validate_request_limit(self):
        with self.lock:
            now = time.time()

            while len(self.calls) > 0 and self._should_remove(self.calls[0], now):
                self.calls.popleft()

            if len(self.calls) >= self.max_requests:
                raise USDAAPIRateLimitError()

            logger.debug(f"Recording API call at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))}")
            self.calls.append(now)

    async def validate_request_limit_async(self):
        async with self.asyncio_lock:
            now = time.time()

            while len(self.calls) > 0 and self._should_remove(self.calls[0], now):
                self.calls.popleft()

            if len(self.calls) >= self.max_requests:
                raise USDAAPIRateLimitError()

            logger.debug(f"Recording API call at {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(now))}")
            self.calls.append(now)

    def _should_remove(self, timestamp: float, now: float) -> bool:
        return timestamp <= now - self.requests_interval
