"""Minimal local WebSocket manager using only the Python standard library."""

from __future__ import annotations

import base64
import hashlib
import json
import socket
import struct
from threading import RLock
from typing import Any


WEBSOCKET_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class WebSocketManager:
    """Track connected local browsers and broadcast text frames."""

    def __init__(self, *, send_timeout_seconds: float = 0.25) -> None:
        self._clients: set[socket.socket] = set()
        self._lock = RLock()
        self.send_timeout_seconds = send_timeout_seconds

    def accept(self, request_handler: Any, initial_payload: dict[str, Any]) -> None:
        """Upgrade an HTTP handler connection to WebSocket and keep it open."""

        key = request_handler.headers.get("Sec-WebSocket-Key")
        if not key:
            request_handler.send_error(400, "Missing WebSocket key")
            return

        accept = base64.b64encode(
            hashlib.sha1(f"{key}{WEBSOCKET_GUID}".encode("ascii")).digest()
        ).decode("ascii")
        request_handler.request.sendall(
            (
                "HTTP/1.1 101 Switching Protocols\r\n"
                "Upgrade: websocket\r\n"
                "Connection: Upgrade\r\n"
                f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
            ).encode("ascii")
        )

        client = request_handler.request
        client.settimeout(0.5)
        with self._lock:
            self._clients.add(client)

        self.send_json(client, initial_payload)
        try:
            while getattr(request_handler.server, "web_running", False):
                try:
                    data = client.recv(2)
                except socket.timeout:
                    continue
                except (ConnectionResetError, OSError):
                    break
                if not data:
                    break
                opcode = data[0] & 0x0F
                length = data[1] & 0x7F
                if length == 126:
                    client.recv(2)
                elif length == 127:
                    client.recv(8)
                masked = data[1] & 0x80
                if masked:
                    mask = client.recv(4)
                    payload = client.recv(length) if length < 126 else b""
                    _ = bytes(byte ^ mask[index % 4] for index, byte in enumerate(payload))
                if opcode == 0x8:
                    break
        finally:
            with self._lock:
                self._clients.discard(client)
            try:
                client.close()
            except OSError:
                pass

    def broadcast_json(self, payload: dict[str, Any]) -> None:
        """Send JSON to every connected browser."""

        with self._lock:
            clients = list(self._clients)
        for client in clients:
            if not self.send_json(client, payload):
                with self._lock:
                    self._clients.discard(client)

    def send_json(self, client: socket.socket, payload: dict[str, Any]) -> bool:
        """Send one JSON text frame."""

        try:
            client.settimeout(self.send_timeout_seconds)
            client.sendall(self._encode_text(json.dumps(payload, ensure_ascii=True)))
            return True
        except (OSError, socket.timeout):
            return False

    def close_all(self) -> None:
        """Close all open browser sockets."""

        with self._lock:
            clients = list(self._clients)
            self._clients.clear()
        for client in clients:
            try:
                client.close()
            except OSError:
                pass

    def count(self) -> int:
        """Return connected browser count."""

        with self._lock:
            return len(self._clients)

    def _encode_text(self, text: str) -> bytes:
        """Encode a server-to-client WebSocket text frame."""

        payload = text.encode("utf-8")
        length = len(payload)
        if length < 126:
            header = struct.pack("!BB", 0x81, length)
        elif length < 65536:
            header = struct.pack("!BBH", 0x81, 126, length)
        else:
            header = struct.pack("!BBQ", 0x81, 127, length)
        return header + payload
