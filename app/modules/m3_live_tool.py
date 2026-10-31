import json
from fastapi import WebSocket

async def handle_live_companion_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            if msg.get("type") == "INTERRUPT":
                await websocket.send_json({"type": "PLAYBACK_STOP", "message": "已为您暂停播放"})
            else:
                await websocket.send_json({
                    "type": "AUDIO_CHUNK",
                    "text_caption": "这张照片是98年在北海公园拍的吧？看您笑得多开心呀。",
                    "barge_in_ready": True
                })
    except Exception:
        await websocket.close()
