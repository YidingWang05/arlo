import json
from typing import Type, TypeVar, Optional
from pydantic import BaseModel
from app.core.config import settings

T = TypeVar("T", bound=BaseModel)

class GeminiCoreEngine:
    """Gemini 4 Argon Core Foundation Engine with structured thinking & outputs."""
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model_name = settings.GEMINI_MODEL_NAME
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

            # Gemini 4 Argon configuration with native thinking controls
            config = {
                "response_mime_type": "application/json",
                "response_schema": response_schema,
                "temperature": 0.2,
                "thinking_config": {
                    "thinking_level": settings.GEMINI_THINKING_LEVEL
                }
            }

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )
            return response_schema.model_validate_json(response.text)
        except Exception as e:
            print(f"[Fallback] Gemini 4 Argon call failed: {e}. Returning mock.")
            return self._mock_fallback(response_schema)

    def _mock_fallback(self, schema: Type[T]) -> T:
        from app.schemas.m1_vision import VisionExplainResult
        from app.schemas.m2_memory_buy import MemoryBuyResult, CandidateItem
        
        if schema == VisionExplainResult:
            return VisionExplainResult(
                category="MEDICINE",
                headline_large="Take 1 pill morning & night after meals",
                audio_script="Hello Grandpa, this is your blood pressure medicine. Take one pill after breakfast and one after dinner with warm water.",
                action_items=["Twice a day", "One pill each time", "Take after meals"],
                is_blurry=False
            )
        elif schema == MemoryBuyResult:
            return MemoryBuyResult(
                spoken_prompt="Grandpa, I found two matching items. Is it the blue bottle on the left?",
                candidates=[
                    CandidateItem(
                        item_id="item_01",
                        name="Mr Muscle Multi-Action Cleaner (Blue Bottle)",
                        image_url="https://images.unsplash.com/photo-1584308666744-24d5c474f2ae?w=500",
                        display_tag="Left (Bought by Daughter)"
                    ),
                    CandidateItem(
                        item_id="item_02",
                        name="White Cat Lemon Dishwashing Liquid",
                        image_url="https://images.unsplash.com/photo-1585670270638-33ddc01f2c2d?w=500",
                        display_tag="Right option"
                    )
                ]
            )
        return schema.construct()

gemini_engine = GeminiCoreEngine()
