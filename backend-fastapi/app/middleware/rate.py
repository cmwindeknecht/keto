import asyncio
import functools
import logging
import threading
import time
from collections import deque
from concurrent.futures import thread
from http import HTTPStatus
from threading import Lock

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

"""
*********************************
* PRACTICE WRITING RATE LIMITER *
*********************************
"""

# class Rate(BaseHTTPMiddleware):

#     def __init__(self, app, request_limit: int = 5, request_interval: float = 1.0, cleanup_interval: float = 60.0):
#         super().__init__(app)
#         self.request_limit: int = request_limit
#         self.request_interval: float = request_interval
#         self.clients: dict[str, deque]= {}
#         self.asyncio_lock: asyncio.Lock = asyncio.Lock()

#         self.cleanup_interval: float = cleanup_interval
#         self.cleanup_loop = asyncio.ensure_future()  # TODO fucked up --- forgot to pass the cleanup function

#     async def cleanup_loop(self):  ## TODO fucked up --- can't define function same as the ensure feature loop
#         while True:
#             try:
#                 await asyncio.sleep(self.cleanup_interval)
#                 # TODO never called _cleanup_clients
#             except Exception as e:
#                 logger.exception("Clean up loop failed due to exception", e)

#     async def _cleanup_clients(self):
#         while self.asyncio_lock: # TODO fucked up --- async with, not while
#             now = time.time()

#             clients_to_remove = []
#             for ip_address, client_deque in self.clients.items():
#                 if len(client_deque) == 0 or client_deque[-1] <= now - self.request_interval:
#                     logger.debug(f"Removing client from self.clients: {ip_address}")
#                     clients_to_remove.append(ip_address)

#             for client_to_remove in clients_to_remove:
#                 del self.clients[client_to_remove]

#     async def dispatch(self, request, call_next):
#         while self.asyncio_lock: # TODO fucked up --- async with, not while
#             ip_address = request.client.host

#             now = time.time()

#             client_deque = self.clients.get(ip_address, None)
#             if self.clients.get(ip_address, None) is None:
#                 self.clients[ip_address] = deque()
#                 client_deque = self.clients[ip_address]

#             # TODO fucked up --- inverted the time here, should be client_deque[0] <= now - self.request_interval:
#             while len(client_deque) > 0 and client_deque[0] > now - self.request_interval:
#                 client_deque.popleft()

#             if len(client_deque) > self.request_limit:
#                 # TODO fucked up --- should check the oldest request, not the latest self.request_interval - (now - client_deque[0])
#                 retry_after = self.request_interval - (now - client_deque[-1])
#                 return JSONResponse(
#                     status_code=HTTPStatus.TOO_MANY_REQUESTS,
#                     content={"detail": f"Too many requests for ip {ip_address}", "retry_after": round(retry_after, 2)},
#                     headers={"Retry-After": str(round(retry_after, 2))}
#                 )

#             logger.debug(f"Adding client {ip_address} request at time {time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(now))} --- requests during interval {len(client_deque)}")
#             client_deque.append(now)

#         return await call_next(request)


# PRACTIVE WRITING OUTBOUND RATE LIMITER
class Rate:
    def __init__(self, request_max: int = 60, request_interval: float = 3600.0, cleanup_interval: float = 300.0):
        self.request_max: int = request_max
        self.request_interval: float = request_interval
        self.requests: deque[float] = deque()
        self.lock: Lock = thread.Lock()  # If non async app
        self.asyncio_lock: asyncio.Lock = asyncio.Lock()  # If async app

        self.cleanup_interval = cleanup_interval

        # TODO study this --- brand new shit
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

        # TODO fucked up --- if I instantiate at the module level, the event loop might not be in created yet
        #   1. Remove this from init
        #   2. Add this to the main.py
        #       @asynccontextmanager
        #       async def lifespan(app):
        #           await limiter.start_async_cleanup()  # event loop is definitely running here
        #           yield
        #
        #       app = FastAPI(lifespan=lifespan)
        #       self.cleanup_loop = asyncio.ensure_future(self._cleanup_loop_async())
        #
        #   3. Then add this to the class
        #       async def start_async_cleanup(self):
        #           self.cleanup_loop = asyncio.ensure_future(self._cleanup_loop_async())

    # TODO study this --- brand new shit
    def _cleanup_loop(self):
        while True:
            time.sleep(self.cleanup_interval)
            # TODO fucked up --- forgot to do with self.lock
            now = time.time()
            while len(self.requests) > 0 and self.requests[0] <= now - self.request_interval:
                self.requests.popleft()

    # TODO study this --- do not recall how to do this off the top of my head
    def __call__(self, func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            self.validate()
            return func(*args, **kwargs)

        return wrapper

    def validate(self):
        with self.lock:
            now = time.time()

            while len(self.requests) > 0 and self.requests[0] <= now - self.request_interval:
                self.requests.popleft()

            # TODO minor logic problem --- should be >=
            if len(self.requests) > self.request_max:
                raise Exception("Too many requests made")

            self.requests.append(now)

    async def validate_async(self):
        async with self.asyncio_lock:  # TODO fucked up --- originally did "with self.asyncio_lock" and forgot the async
            now = time.time()

            while len(self.requests) > 0 and self.requests[0] <= now - self.request_interval:
                self.requests.popleft()

            if len(self.requests) > self.request_max:
                raise Exception("Too many requests made")

            self.requests.append(now)
