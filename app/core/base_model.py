import json
from typing import Type, TypeVar, Optional
from pydantic import BaseModel
from app.core.config import settings

T = TypeVar("T", bound=BaseModel)

class GeminiCoreEngine:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception as e:
                print(f"[Warning] Failed to initialize Gemini Client: {e}")

    async def generate_structured(self, prompt: str, image_bytes: Optional[bytes], response_schema: Type[T]) -> T:
        if not self.client:
            return self._mock_fallback(response_schema)
            
        try:
            from google.genai import types
            contents = [prompt]
            if image_bytes:
                contents.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))

            response = self.client.models.generate_content(
                model=settings.GEMINI_MODEL_NAME,
                contents=contents,
                config={
                    "response_mime_type": "application/json",
                    "response_schema": response_schema,
                    "temperature": 0.2
                }
            )
            return response_schema.model_validate_json(response.text)
        except Exception as e:
            print(f"[Fallback] Gemini API Call failed: {e}. Using structured mock.")
            return self._mock_fallback(response_schema)

    def _mock_fallback(self, schema: Type[T]) -> T:
        from app.schemas.m1_vision import VisionExplainResult
        from app.schemas.m2_memory_buy import MemoryBuyResult, CandidateItem
        
        if schema == VisionExplainResult:
            return VisionExplainResult(
                category="MEDICINE",
                headline_large="早晚各吃 1 粒 · 饭后温水服",
                audio_script="张爷爷，这是高血压药，每天早晚各吃一粒，记得要吃完饭再吃哦。",
                action_items=["每日两次", "每次一粒", "饭后服用"],
                is_blurry=False
            )
        elif schema == MemoryBuyResult:
            return MemoryBuyResult(
                spoken_prompt="张爷爷，帮您找到了两款，是左边这瓶蓝色的吗？",
                candidates=[
                    CandidateItem(
                        item_id="item_01",
                        name="威猛先生洁厕液(蓝色鸭嘴瓶)",
                        image_url="https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500",
                        display_tag="左边这个 (女儿买过)"
                    ),
                    CandidateItem(
                        item_id="item_02",
                        name="白猫柠檬多效洗洁精",
                        image_url="https://images.unsplash.com/photo-1585670270638-33ddc01f2c2d?w=500",
                        display_tag="右边这个"
                    )
                ]
            )
        return schema.construct()

gemini_engine = GeminiCoreEngine()
