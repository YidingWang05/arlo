"""Offline M3 protocol tests, isolated from the shared Gemini client and keys."""

import pytest

from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient

from app.modules.m3_live_tool import (
    Story, demo_story_provider, handle_live_companion_stream,
)


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


def start_story(socket, **fields):
    """Send a standard caption-only story request."""
    socket.send_json({
        "type": "START_STORY", "photo_id": "photo-1",
        "caption": "A garden full of flowers.", **fields,
    })


def receive_story(socket):
    """Collect a finite stream and fail on any unexpected intermediate event."""
    started = socket.receive_json()
    assert started["type"] == "STORY_STARTED"
    chunks = []
    while True:
        message = socket.receive_json()
        assert message["story_id"] == started["story_id"]
        assert message["session_id"] == started["session_id"]
        if message["type"] == "STORY_COMPLETE":
            return started, chunks, message
        assert message["type"] == "CAPTION_CHUNK"
        chunks.append(message)


def test_start_story_streams_ordered_captions_and_completes():
    with make_client(story_provider=demo_story_provider, chunk_delay=0.001) as client:
        with client.websocket_connect("/live/ws") as socket:
            socket.receive_json()
            start_story(socket)
            _, chunks, complete = receive_story(socket)
            assert [chunk["sequence"] for chunk in chunks] == list(range(1, len(chunks) + 1))
            assert chunks and all(chunk["barge_in_ready"] for chunk in chunks)
            assert all(chunk["source"] == "demo" for chunk in chunks)
            assert complete["source"] == "demo"
            assert "garden" in " ".join(chunk["text"] for chunk in chunks)


def test_story_is_bounded_below_ninety_words():
    async def long_provider(request):
        return Story("word " * 200)

    with make_client(story_provider=long_provider, chunk_delay=0.001) as client:
        with client.websocket_connect("/live/ws") as socket:
            socket.receive_json()
            start_story(socket)
            _, chunks, _ = receive_story(socket)
            assert sum(len(chunk["text"].split()) for chunk in chunks) == 89
            assert all(len(chunk["text"].split()) <= 18 for chunk in chunks)
