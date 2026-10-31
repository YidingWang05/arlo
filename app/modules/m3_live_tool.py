"""M3 application WebSocket transport; browser speech supplies audible playback.

Each connection owns its session. This endpoint does not open a Gemini Live API
session, and accepts its socket exactly once.
"""

from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect


async def handle_live_companion_stream(websocket: WebSocket):
    """Accept a connection and exchange session-scoped control messages."""
    await websocket.accept()
    session_id = uuid4().hex
    try:
        await websocket.send_json({"type": "SESSION_READY", "session_id": session_id})
        while True:
            message = await websocket.receive_json()
            if message.get("type") == "PING":
                await websocket.send_json({"type": "PONG", "session_id": session_id})
    except WebSocketDisconnect:
        # A disconnected socket must not be closed a second time.
        return
