from app.schemas.m1_vision import VisionExplainResult
from app.core.base_model import gemini_engine

SYSTEM_PROMPT = """
You are an expert geriatric care and everyday living assistant powered by Gemini 4 Argon.
When an older adult shows a prescription, label, or bill to the camera:
1. Filter out complex chemical formulas and bureaucratic legal text.
2. Extract the core practical instructions (dosage, frequency, timing, or payment amount).
3. Ensure 'headline_large' is under 15 plain words so it can be easily read in 48px+ font.
4. Ensure 'audio_script' uses warm, empathetic, and clear conversational phrasing for audio playback.
"""

async def run_vision_explain(image_bytes: bytes, user_query: str) -> VisionExplainResult:
    prompt = f"{SYSTEM_PROMPT}\nUser voice query: {user_query}"
    return await gemini_engine.generate_structured(prompt, image_bytes, VisionExplainResult)
