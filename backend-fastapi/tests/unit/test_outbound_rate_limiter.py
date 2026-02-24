"""Unit tests for OutboundRateLimiter."""

import time

import pytest

from app.core.exceptions import USDAAPIRateLimitError
from app.routes.outbound_rate_limiter import OutboundRateLimiter


def test_sync_within_limit():
    limiter = OutboundRateLimiter(max_requests=3, requests_interval=60.0)

    @limiter
    def fn():
        return "ok"

    for _ in range(3):
        assert fn() == "ok"


def test_sync_exceeds_limit():
    limiter = OutboundRateLimiter(max_requests=2, requests_interval=60.0)

    @limiter
    def fn():
        return "ok"

    fn()
    fn()
    with pytest.raises(USDAAPIRateLimitError):
        fn()


async def test_async_within_limit():
    limiter = OutboundRateLimiter(max_requests=3, requests_interval=60.0)

    @limiter
    async def fn():
        return "ok"

    for _ in range(3):
        assert await fn() == "ok"


async def test_async_exceeds_limit():
    limiter = OutboundRateLimiter(max_requests=2, requests_interval=60.0)

    @limiter
    async def fn():
        return "ok"

    await fn()
    await fn()
    with pytest.raises(USDAAPIRateLimitError):
        await fn()


def test_sync_resets_after_window():
    limiter = OutboundRateLimiter(max_requests=2, requests_interval=0.1)

    @limiter
    def fn():
        return "ok"

    fn()
    fn()
    with pytest.raises(USDAAPIRateLimitError):
        fn()
    time.sleep(0.15)
    assert fn() == "ok"


async def test_async_resets_after_window():
    limiter = OutboundRateLimiter(max_requests=2, requests_interval=0.1)

    @limiter
    async def fn():
        return "ok"

    await fn()
    await fn()
    with pytest.raises(USDAAPIRateLimitError):
        await fn()
    time.sleep(0.15)
    assert await fn() == "ok"


def test_validate_request_limit_tracks_calls():
    limiter = OutboundRateLimiter(max_requests=5, requests_interval=60.0)
    for _ in range(4):
        limiter.validate_request_limit()
    assert len(limiter.calls) == 4


def test_validate_request_limit_raises_at_max():
    limiter = OutboundRateLimiter(max_requests=2, requests_interval=60.0)
    limiter.validate_request_limit()
    limiter.validate_request_limit()
    with pytest.raises(USDAAPIRateLimitError):
        limiter.validate_request_limit()


async def test_validate_request_limit_async_raises_at_max():
    limiter = OutboundRateLimiter(max_requests=2, requests_interval=60.0)
    await limiter.validate_request_limit_async()
    await limiter.validate_request_limit_async()
    with pytest.raises(USDAAPIRateLimitError):
        await limiter.validate_request_limit_async()


def test_should_remove_old_timestamp():
    limiter = OutboundRateLimiter(requests_interval=60.0)
    assert limiter._should_remove(time.time() - 61.0, time.time()) is True


def test_should_not_remove_recent_timestamp():
    limiter = OutboundRateLimiter(requests_interval=60.0)
    assert limiter._should_remove(time.time() - 30.0, time.time()) is False


def test_preserves_return_value():
    limiter = OutboundRateLimiter(max_requests=10, requests_interval=60.0)

    @limiter
    def add(x, y):
        return x + y

    assert add(2, 3) == 5


async def test_preserves_async_return_value():
    limiter = OutboundRateLimiter(max_requests=10, requests_interval=60.0)

    @limiter
    async def add(x, y):
        return x + y

    assert await add(2, 3) == 5
