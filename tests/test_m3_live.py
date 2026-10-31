"""Offline M3 protocol tests, isolated from the shared Gemini client and keys."""

import pytest

from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient

from app.modules.m3_live_tool import handle_live_companion_stream


def make_client(**options):
    """Mount only M3 so no other module can spend API credits during tests."""
    app = FastAPI()

    @app.websocket("/live/ws")
    async def live(websocket: WebSocket):
        await handle_live_companion_stream(websocket, **options)

    return TestClient(app)


def test_connection_ready_and_ping():
    with make_client() as client, client.websocket_connect("/live/ws") as socket:
        ready = socket.receive_json()
        assert ready["type"] == "SESSION_READY"
        assert ready["session_id"]
        socket.send_json({"type": "PING"})
        assert socket.receive_json() == {
            "type": "PONG", "session_id": ready["session_id"]
        }


def test_connections_have_independent_sessions():
    with make_client() as client:
        with client.websocket_connect("/live/ws") as first:
            with client.websocket_connect("/live/ws") as second:
                assert first.receive_json()["session_id"] != second.receive_json()["session_id"]


def test_disconnect_exits_cleanly():
    with make_client() as client:
        with client.websocket_connect("/live/ws") as socket:
            assert socket.receive_json()["type"] == "SESSION_READY"


@pytest.mark.parametrize("raw", [
    "{broken", "[]", "null", '{"type": []}', '{"type": "UNKNOWN"}',
    '{"type": "START_STORY", "photo_id": "p"}',
    '{"type": "START_STORY", "photo_id": "p", "caption": ""}',
    '{"type": "USER_TEXT", "text": 5}',
    '{"type": "START_STORY", "photo_id": "p", "caption": "c", "user_prompt": []}',
    '{"type": "PING", "session_id": "someone-else"}',
    "x" * 16_385,
    '{"type":"PING","padding":"' + "\u4f60" * 6_000 + '"}',
    "[" * 1_100 + "]" * 1_100,
])
def test_invalid_message_returns_error_and_connection_survives(raw):
    with make_client() as client, client.websocket_connect("/live/ws") as socket:
        ready = socket.receive_json()
        socket.send_text(raw)
        error = socket.receive_json()
        assert error["type"] == "ERROR"
        assert error["session_id"] == ready["session_id"]
        assert error["message"]
        socket.send_json({"type": "PING"})
        assert socket.receive_json()["type"] == "PONG"


def test_binary_message_returns_error():
    with make_client() as client, client.websocket_connect("/live/ws") as socket:
        socket.receive_json()
        socket.send_bytes(b"binary audio is not the MVP protocol")
        assert socket.receive_json()["type"] == "ERROR"
        socket.send_json({"type": "PING"})
        assert socket.receive_json()["type"] == "PONG"
