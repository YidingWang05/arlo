"""M3 application WebSocket transport; browser speech supplies audible playback.

Each connection owns its session. This endpoint does not open a Gemini Live API
session, and accepts its socket exactly once.
"""

import asyncio
import json
import logging
import re
from contextlib import suppress
from dataclasses import dataclass
from typing import Awaitable, Callable
from uuid import uuid4

from fastapi import WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState

logger = logging.getLogger(__name__)

MAX_MESSAGE_BYTES = 16_384
MESSAGE_FIELDS = {
    "PING": (),
    "INTERRUPT": (),
    "START_STORY": ("photo_id", "caption"),
    "USER_TEXT": ("text",),
}


@dataclass(frozen=True)
class StoryRequest:
    """Caption context supplied by this connection, never fetched across users."""

    photo_id: str
    caption: str
    user_prompt: str = ""


@dataclass(frozen=True)
class Story:
    """Short provider response with an explicit origin for honest demo labels."""

    text: str
    source: str = "demo"


StoryProvider = Callable[[StoryRequest], Awaitable[Story]]


async def demo_story_provider(request: StoryRequest) -> Story:
    """Deterministic opt-in demo data; never presented as a Gemini result."""
    return Story(
        f"The supplied caption says: {request.caption} "
        "We can take a quiet moment with this photo. "
        "What would you like to tell me about it?",
        source="demo",
    )


async def unavailable_story_provider(request: StoryRequest) -> Story:
    """Fail visibly until the shared core text-generation interface is ready."""
    raise RuntimeError("Shared story provider is not configured")


def story_chunks(story: Story) -> list[str]:
    """Bound stories below 90 words and form natural chunks of up to 18 words."""
    if not isinstance(story, Story) or story.source not in {"demo", "argon"}:
        raise ValueError("Invalid story provider response")
    if not isinstance(story.text, str) or not story.text.strip():
        raise ValueError("Story provider returned empty text")
    text = " ".join(story.text.split()[:89])
    chunks = []
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        words = sentence.split()
        chunks.extend(" ".join(words[i:i + 18]) for i in range(0, len(words), 18))
    return chunks


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


async def handle_live_companion_stream(
    websocket: WebSocket,
    *,
    story_provider: StoryProvider | None = None,
    chunk_delay: float = 0.2,
    generation_timeout: float = 20.0,
):
    """Receive controls concurrently with one cancellable story per connection."""
    await websocket.accept()
    session_id = uuid4().hex
    provider = story_provider or unavailable_story_provider
    active_task = None
    send_lock = asyncio.Lock()

    async def send(message_type: str, **fields):
        """Serialize outbound events and avoid sends after a known disconnect."""
        async with send_lock:
            if websocket.client_state != WebSocketState.CONNECTED:
                raise WebSocketDisconnect()
            await websocket.send_json({
                "type": message_type, "session_id": session_id, **fields
            })

    async def cancel_active():
        """Join the task so no old captions escape after cancellation returns."""
        nonlocal active_task
        if active_task is not None:
            active_task.cancel()
            with suppress(asyncio.CancelledError, WebSocketDisconnect, OSError):
                await active_task
            active_task = None

    async def stream_story(request: StoryRequest, story_id: str):
        """Generate one bounded story and stream captions without blocking input."""
        try:
            await send("STORY_STARTED", story_id=story_id, photo_id=request.photo_id)
            story = await asyncio.wait_for(provider(request), generation_timeout)
            chunks = story_chunks(story)
            for sequence, text in enumerate(chunks, start=1):
                await send(
                    "CAPTION_CHUNK", story_id=story_id, sequence=sequence,
                    text=text, barge_in_ready=True, source=story.source,
                )
                if sequence < len(chunks):
                    await asyncio.sleep(chunk_delay)
            await send("STORY_COMPLETE", story_id=story_id, source=story.source)
        except (WebSocketDisconnect, OSError):
            logger.info("M3 story transport disconnected")
        except Exception as error:
            # Exception text and traceback may contain prompts, keys or captions.
            logger.warning("M3 story failed (%s)", type(error).__name__)
            try:
                await send("ERROR", story_id=story_id,
                           message="The story is unavailable. Please try again.")
            except (WebSocketDisconnect, OSError):
                logger.info("M3 error transport disconnected")

    try:
        await send("SESSION_READY")
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
                await send("ERROR", message=str(error))
                continue
            if message.get("type") == "PING":
                await send("PONG")
            elif message["type"] == "START_STORY":
                await cancel_active()
                request = StoryRequest(
                    message["photo_id"], message["caption"], message.get("user_prompt", "")
                )
                active_task = asyncio.create_task(stream_story(request, uuid4().hex))
    except (WebSocketDisconnect, OSError):
        logger.info("M3 session disconnected")
    finally:
        await cancel_active()
