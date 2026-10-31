from fastapi import APIRouter, UploadFile, File, Form, WebSocket, HTTPException
import logging

logger = logging.getLogger(__name__)
from app.schemas.common import BaseResponse
from app.schemas.m1_vision import VisionExplainResult
from app.schemas.m2_memory_buy import MemoryBuyRequest, MemoryBuyResult
from app.schemas.m4_frame import FamilyPhotoPush, FramePhotoItem
from app.modules.m1_vision_tool import run_vision_explain
from app.modules.m2_memory_tool import run_memory_buy
from app.modules.m3_live_tool import handle_live_companion_stream
from app.modules.m4_frame_hub import push_family_photo, get_frame_photos

router = APIRouter(prefix="/api/arlo", tags=["Arlo Multimodal Framework"])

@router.post("/vision/explain", response_model=BaseResponse[VisionExplainResult])
async def api_vision_explain(file: UploadFile = File(...), query: str = Form("How should I take this medicine?")):
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(400, "Upload a JPEG, PNG, or WEBP image")
    image_bytes = await file.read(10 * 1024 * 1024 + 1)
    if len(image_bytes) > 10 * 1024 * 1024:
        raise HTTPException(413, "Image exceeds the 10 MB limit")
    if not image_bytes:
        raise HTTPException(400, "Image is empty")
    result = await run_vision_explain(image_bytes, query)
    return BaseResponse(data=result)

@router.post("/memory/buy", response_model=BaseResponse[MemoryBuyResult])
async def api_memory_buy(req: MemoryBuyRequest):
    try:
        result = await run_memory_buy(req.speech_query)
    except TimeoutError:
        raise HTTPException(504, "Memory lookup timed out; please retry") from None
    except ConnectionError:
        raise HTTPException(503, "Memory lookup unavailable; please retry") from None
    except Exception as exc:
        logger.error("Memory lookup failed (%s)", type(exc).__name__)
        raise HTTPException(500, "Memory lookup failed") from None
    return BaseResponse(data=result)

@router.websocket("/live/ws")
async def api_live_ws(websocket: WebSocket):
    await handle_live_companion_stream(websocket)

@router.post("/frame/photo-push", response_model=BaseResponse[bool])
async def api_push_photo(req: FamilyPhotoPush):
    ok = await push_family_photo(req)
    return BaseResponse(data=ok)

@router.get("/frame/photos", response_model=BaseResponse[list[FramePhotoItem]])
async def api_get_photos():
    photos = await get_frame_photos()
    return BaseResponse(data=photos)
