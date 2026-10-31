import json
from fastapi import WebSocket

async def handle_live_companion_stream(websocket: WebSocket):
    """Module 3: Full-duplex live companion with natural barge-in interruption support."""
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "INTERRUPT":
                await websocket.send_json({"type": "PLAYBACK_STOP", "message": "Playback paused for listening"})
            else:
                await websocket.send_json({
                    "type": "AUDIO_CHUNK",
                    "text_caption": "Was this photo taken at the lake park back in 1998? Everyone looked so happy!",
                    "barge_in_ready": True
                })
    except Exception:
        await websocket.close()
