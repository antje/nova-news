from __future__ import annotations

import asyncio
import json
import weakref
from typing import Dict, Optional

from fastapi import WebSocket


class WebSocketNotifier:
    """Manages WebSocket connections keyed by job_id and dispatches updates."""

    def __init__(self) -> None:
        self._connections: Dict[str, weakref.WeakSet] = {}
        self._lock = asyncio.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    async def add_connection(self, job_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            if self._loop is None:
                try:
                    self._loop = asyncio.get_running_loop()
                except RuntimeError:
                    self._loop = None
            if job_id not in self._connections:
                self._connections[job_id] = weakref.WeakSet()
            self._connections[job_id].add(websocket)

    async def remove_connection(self, job_id: str, websocket: WebSocket) -> None:
        async with self._lock:
            if job_id in self._connections:
                try:
                    self._connections[job_id].discard(websocket)
                    if not self._connections[job_id]:
                        del self._connections[job_id]
                except KeyError:
                    pass

    async def notify_job_update(self, job_id: str, message_type: str, data: object) -> None:
        async with self._lock:
            if job_id not in self._connections:
                return
            message = json.dumps({"type": message_type, "data": data})
            connections = list(self._connections[job_id])
        for websocket in connections:
            try:
                await websocket.send_text(message)
            except Exception:
                continue

    def notify_job_update_sync(self, job_id: str, message_type: str, data: object) -> None:
        loop = self._loop
        if loop and loop.is_running():
            try:
                asyncio.run_coroutine_threadsafe(
                    self.notify_job_update(job_id, message_type, data),
                    loop,
                )
            except Exception:
                return
            return
        try:
            running_loop = asyncio.get_running_loop()
            running_loop.create_task(
                self.notify_job_update(job_id, message_type, data)
            )
        except RuntimeError:
            return


websocket_notifier = WebSocketNotifier()
