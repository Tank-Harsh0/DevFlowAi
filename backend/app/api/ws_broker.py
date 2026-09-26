"""
WebSocket event broker.

A lightweight in-process pub/sub system so background threads can push
WorkflowEvent dicts to connected WebSocket clients without any external
message broker.

Usage
-----
Publish from a (sync) background thread::

    ws_broker.publish(workflow_id, event_dict)

Subscribe from an async WebSocket handler::

    async with ws_broker.subscribe(workflow_id) as queue:
        event = await queue.get()
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator


class _WsBroker:
    def __init__(self) -> None:
        # workflow_id → set of asyncio.Queue instances (one per connected client)
        self._subscribers: dict[str, set[asyncio.Queue[Any]]] = defaultdict(set)
        # The running event loop — captured on first publish so sync threads can reach it.
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Called once from the FastAPI lifespan to capture the event loop."""
        self._loop = loop

    def publish(self, workflow_id: str, event: dict[str, Any]) -> None:
        """Push *event* to all queues subscribed to *workflow_id*.

        Safe to call from any thread (uses call_soon_threadsafe).
        """
        if self._loop is None:
            return
        loop = self._loop
        subs = self._subscribers.get(workflow_id)
        if not subs:
            return

        def _enqueue() -> None:
            for q in list(subs):
                q.put_nowait(event)

        loop.call_soon_threadsafe(_enqueue)

    @asynccontextmanager
    async def subscribe(
        self, workflow_id: str
    ) -> AsyncGenerator[asyncio.Queue[Any], None]:
        """Async context manager: register a queue and yield it; clean up on exit."""
        q: asyncio.Queue[Any] = asyncio.Queue()
        self._subscribers[workflow_id].add(q)
        try:
            yield q
        finally:
            self._subscribers[workflow_id].discard(q)
            if not self._subscribers[workflow_id]:
                del self._subscribers[workflow_id]


ws_broker = _WsBroker()
