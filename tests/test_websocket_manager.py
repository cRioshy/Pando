"""Tests for resilient WebSocket broadcasts."""

from __future__ import annotations

import socket
import unittest

from web.websocket_manager import WebSocketManager


class BlockingSocket:
    """Socket-like object that always times out on send."""

    def __init__(self) -> None:
        self.timeout: float | None = None

    def settimeout(self, value: float) -> None:
        self.timeout = value

    def sendall(self, payload: bytes) -> None:
        raise socket.timeout("simulated blocked browser socket")


class WebSocketManagerTest(unittest.TestCase):
    def test_blocked_socket_is_removed_from_broadcast_clients(self) -> None:
        manager = WebSocketManager(send_timeout_seconds=0.01)
        blocked = BlockingSocket()
        with manager._lock:
            manager._clients.add(blocked)  # type: ignore[arg-type]

        manager.broadcast_json({"type": "event"})

        self.assertEqual(manager.count(), 0)
        self.assertEqual(blocked.timeout, 0.01)


if __name__ == "__main__":
    unittest.main()
