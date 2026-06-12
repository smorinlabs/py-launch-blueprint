# Copyright (c) 2025, Steve Morin
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

"""Idempotency-Key replay protection for unsafe methods (WEB-05).

A client that retries a ``POST``/``PUT``/``PATCH`` with the same
``Idempotency-Key`` header gets the cached first response back (marked with
``Idempotency-Replayed: true``) instead of re-executing the side effect.

The store is per-process and in-memory: TTL-bounded, LRU-capped, and suitable
for a single instance. Swap in a Redis-backed store before scaling out —
the cache key and entry shapes here are the contract for that. Concurrent
duplicates (second request arriving before the first finishes) are NOT
single-flighted; that also needs the shared store.
"""

import time
from collections import OrderedDict
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

IDEMPOTENCY_HEADER = "idempotency-key"
REPLAYED_HEADER = "idempotency-replayed"
_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH"})

#: (stored_at_monotonic, status_code, headers, body)
_Entry = tuple[float, int, dict[str, str], bytes]


class IdempotencyMiddleware(BaseHTTPMiddleware):
    """Cache and replay successful responses keyed by Idempotency-Key."""

    def __init__(
        self,
        app: ASGIApp,
        ttl_seconds: int = 86400,
        max_entries: int = 1024,
    ) -> None:
        super().__init__(app)
        self.ttl_seconds = ttl_seconds
        self.max_entries = max_entries
        self._store: OrderedDict[tuple[str, str, str], _Entry] = OrderedDict()

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        key = request.headers.get(IDEMPOTENCY_HEADER)
        if not key or request.method not in _UNSAFE_METHODS:
            return await call_next(request)

        cache_key = (request.method, request.url.path, key)
        now = time.monotonic()

        entry = self._store.get(cache_key)
        if entry is not None:
            stored_at, status_code, headers, body = entry
            if now - stored_at < self.ttl_seconds:
                self._store.move_to_end(cache_key)
                replay = Response(
                    content=body, status_code=status_code, headers=headers
                )
                replay.headers[REPLAYED_HEADER] = "true"
                return replay
            del self._store[cache_key]

        response = await call_next(request)
        body = b""
        # call_next really returns a streaming response; Response is the
        # declared (narrower) type, hence the suppression.
        async for chunk in response.body_iterator:  # ty: ignore[unresolved-attribute]
            body += chunk
        rebuilt = Response(
            content=body,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
        # Only successful outcomes are replayable; errors should be retried
        # for real (the Stripe semantics).
        if 200 <= response.status_code < 300:
            self._store[cache_key] = (
                now,
                response.status_code,
                dict(response.headers),
                body,
            )
            while len(self._store) > self.max_entries:
                self._store.popitem(last=False)
        return rebuilt
