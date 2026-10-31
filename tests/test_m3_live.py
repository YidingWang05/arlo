"""Offline M3 protocol tests, isolated from the shared Gemini client and keys."""

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
