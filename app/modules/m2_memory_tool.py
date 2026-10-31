from app.schemas.m2_memory_buy import MemoryBuyResult
from app.core.base_model import gemini_engine

BUY_PROMPT = """
The older adult wants to buy an everyday household item but cannot recall the exact brand or product name.
They describe visual clues (color, shape, packaging) or who bought it before.
Extract visual entities and match against family household memory, returning two candidate images for single-decision confirmation.
"""

async def run_memory_buy(speech_query: str) -> MemoryBuyResult:
    prompt = f"{BUY_PROMPT}\nElderly speech input: '{speech_query}'"
    return await gemini_engine.generate_structured(prompt, None, MemoryBuyResult)
