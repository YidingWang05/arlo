"""M3 application WebSocket transport; browser speech supplies audible playback.

Each connection owns its session. This endpoint does not open a Gemini Live API
session, and accepts its socket exactly once.
"""

import json
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect

MAX_MESSAGE_BYTES = 16_384
MESSAGE_FIELDS = {
    "PING": (),
    "INTERRUPT": (),
    "START_STORY": ("photo_id", "caption"),
    "USER_TEXT": ("text",),
}


def parse_message(raw: str, session_id: str) -> dict:
    """Validate the small JSON envelope without retaining personal content."""
    if len(raw.encode("utf-8")) > MAX_MESSAGE_BYTES:
        raise ValueError("Message is too large. Please send a shorter message.")
    try:
        message = json.loads(raw)
    except (ValueError, RecursionError):
        raise ValueError("Please send a valid JSON message.") from None
    if not isinstance(message, dict):
        raise ValueError("Please send a JSON object.")
    message_type = message.get("type")
    if not isinstance(message_type, str) or message_type not in MESSAGE_FIELDS:
        raise ValueError("This message type is not supported.")
    if "session_id" in message and message["session_id"] != session_id:
        raise ValueError("This message belongs to a different session.")
    for field in MESSAGE_FIELDS[message_type]:
        if not isinstance(message.get(field), str) or not message[field].strip():
            raise ValueError(f"Please provide {field} as non-empty text.")
    if "user_prompt" in message and not isinstance(message["user_prompt"], str):
        raise ValueError("Please provide user_prompt as text.")
    return message


async def handle_live_companion_stream(websocket: WebSocket):
    """Accept a connection and exchange session-scoped control messages."""
    await websocket.accept()
    session_id = uuid4().hex
    try:
        await websocket.send_json({"type": "SESSION_READY", "session_id": session_id})
        while True:
            frame = await websocket.receive()
            if frame["type"] == "websocket.disconnect":
                break
            raw = frame.get("text")
            try:
                if raw is None:
                    raise ValueError("Please send text JSON messages.")
                message = parse_message(raw, session_id)
            except ValueError as error:
                await websocket.send_json({
                    "type": "ERROR", "session_id": session_id, "message": str(error)
                })
                continue
            if message.get("type") == "PING":
                await websocket.send_json({"type": "PONG", "session_id": session_id})
    except WebSocketDisconnect:
        # A disconnected socket must not be closed a second time.
        return
