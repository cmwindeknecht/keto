"""Unit tests for InboundRateLimiterMiddleware."""

import time
from collections import deque
from unittest.mock import MagicMock, patch

from starlette.responses import JSONResponse

from app.middleware.inbound_rate_limiter import InboundRateLimiterMiddleware

# Capture real dispatch before the autouse bypass patches it
_real_dispatch = InboundRateLimiterMiddleware.dispatch


def _make_middleware(requests_limit=5, requests_interval=1.0):
    def _close_coro(coro):
        coro.close()

    with patch("asyncio.ensure_future", side_effect=_close_coro):
        return InboundRateLimiterMiddleware(MagicMock(), requests_limit=requests_limit, requests_interval=requests_interval)


def _make_request(ip="127.0.0.1"):
    req = MagicMock()
    req.client.host = ip
    return req


async def _call_next(request):
    return JSONResponse({"status": "ok"})


def test_should_remove_old_timestamp():
    m = _make_middleware()
    assert m._should_remove(time.time() - 2.0, time.time()) is True


def test_should_not_remove_recent_timestamp():
    m = _make_middleware()
    assert m._should_remove(time.time() - 0.1, time.time()) is False


async def test_allows_requests_within_limit():
    m = _make_middleware(requests_limit=3)
    for _ in range(3):
        r = await _real_dispatch(m, _make_request(), _call_next)
        assert r.status_code == 200


async def test_blocks_requests_exceeding_limit():
    m = _make_middleware(requests_limit=2)
    await _real_dispatch(m, _make_request(), _call_next)
    await _real_dispatch(m, _make_request(), _call_next)
    r = await _real_dispatch(m, _make_request(), _call_next)
    assert r.status_code == 429


async def test_429_response_body():
    import json

    m = _make_middleware(requests_limit=1)
    await _real_dispatch(m, _make_request(), _call_next)
    r = await _real_dispatch(m, _make_request(), _call_next)
    body = json.loads(r.body)
    assert body["error"] == "Rate limit exceeded"
    assert "retry_after" in body


async def test_429_includes_retry_after_header():
    m = _make_middleware(requests_limit=1)
    await _real_dispatch(m, _make_request(), _call_next)
    r = await _real_dispatch(m, _make_request(), _call_next)
    assert "retry-after" in dict(r.headers)


async def test_different_ips_tracked_separately():
    m = _make_middleware(requests_limit=2)
    for ip in ["1.2.3.4", "5.6.7.8"]:
        for _ in range(2):
            r = await _real_dispatch(m, _make_request(ip), _call_next)
            assert r.status_code == 200
    for ip in ["1.2.3.4", "5.6.7.8"]:
        r = await _real_dispatch(m, _make_request(ip), _call_next)
        assert r.status_code == 429


async def test_resets_after_window():
    m = _make_middleware(requests_limit=2, requests_interval=0.1)
    await _real_dispatch(m, _make_request(), _call_next)
    await _real_dispatch(m, _make_request(), _call_next)
    assert (await _real_dispatch(m, _make_request(), _call_next)).status_code == 429
    time.sleep(0.15)
    assert (await _real_dispatch(m, _make_request(), _call_next)).status_code == 200


async def test_cleanup_removes_stale_clients():
    m = _make_middleware(requests_interval=0.1)
    m.clients["1.2.3.4"] = deque([time.time() - 1.0])
    await m._cleanup_stale_clients()
    assert "1.2.3.4" not in m.clients


async def test_cleanup_keeps_active_clients():
    m = _make_middleware(requests_interval=60.0)
    m.clients["1.2.3.4"] = deque([time.time()])
    await m._cleanup_stale_clients()
    assert "1.2.3.4" in m.clients


async def test_cleanup_removes_empty_deques():
    m = _make_middleware()
    m.clients["1.2.3.4"] = deque()
    await m._cleanup_stale_clients()
    assert "1.2.3.4" not in m.clients
