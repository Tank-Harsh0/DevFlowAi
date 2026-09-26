"""
WebSocket router — /api/v1/ws/workflows/{workflow_id}

The frontend connects here to receive live WorkflowEvent messages while
a workflow run is in progress.

Protocol
--------
* Client opens ws://host:8000/api/v1/ws/workflows/{id}
* Server immediately sends the current workflow state as a ``workflow_update``
  event so the page can hydrate without waiting for the next change.
* Server then streams events published by the orchestrator background thread
  until the workflow reaches a terminal state (completed / failed) or the
  client disconnects.
* Event shape mirrors frontend/src/types/workflow.ts ``WorkflowEvent``.
"""
from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.store import store
from app.api.ws_broker import ws_broker
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(tags=["WebSocket"])

_TERMINAL = {"completed", "failed"}
# Maximum seconds to wait for the next event before sending a keepalive ping.
_KEEPALIVE_SECONDS = 20


def _now() -> str:
    return datetime.now(tz=UTC).isoformat()


@router.websocket("/ws/workflows/{workflow_id}")
async def workflow_ws(websocket: WebSocket, workflow_id: str) -> None:
    """Stream live WorkflowEvent messages for *workflow_id*."""
    run = store.workflows.get(workflow_id)
    if run is None:
        # Reject unknown workflow IDs with 404 close code.
        await websocket.close(code=4404, reason="Workflow not found")
        return

    await websocket.accept()
    logger.info("WebSocket client connected for workflow %s", workflow_id)

    try:
        async with ws_broker.subscribe(workflow_id) as queue:
            # ── hydration event ──────────────────────────────────────────────
            # Send the current snapshot so the UI renders immediately.
            initial_run = store.workflows.get(workflow_id)
            if initial_run:
                await websocket.send_text(json.dumps({
                    "type": "workflow_update",
                    "workflowId": workflow_id,
                    "workflow": initial_run.model_dump(),
                    "timestamp": _now(),
                }))

            # ── event stream ─────────────────────────────────────────────────
            while True:
                # Check for terminal state *before* blocking on the queue so
                # we exit cleanly when the workflow finishes with no subscribers.
                current = store.workflows.get(workflow_id)
                if current and current.status in _TERMINAL and queue.empty():
                    # Send a final workflow_update so the UI reflects completion.
                    await websocket.send_text(json.dumps({
                        "type": "workflow_update",
                        "workflowId": workflow_id,
                        "workflow": current.model_dump(),
                        "timestamp": _now(),
                    }))
                    break

                try:
                    event = await asyncio.wait_for(queue.get(), timeout=_KEEPALIVE_SECONDS)
                    await websocket.send_text(json.dumps(event))
                except asyncio.TimeoutError:
                    # Send a keepalive ping so the connection stays alive through
                    # idle stages.  The frontend ignores unrecognised event types.
                    await websocket.send_text(json.dumps({
                        "type": "ping",
                        "workflowId": workflow_id,
                        "timestamp": _now(),
                    }))

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected for workflow %s", workflow_id)
    except Exception as exc:
        logger.warning("WebSocket error for workflow %s: %s", workflow_id, exc)
        try:
            await websocket.close(code=1011)
        except Exception:
            pass
