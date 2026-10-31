from app.schemas.m2_memory_buy import MemoryBuyResult
from app.core.base_model import gemini_engine

BUY_PROMPT = """
老人口述想买某样物品，但可能记不清名字，只记得颜色、外形或谁买过。
请解析其特征，并在家庭记忆知识库中召回最匹配的 2 款商品形成大图二选一。
"""

async def run_memory_buy(speech_query: str) -> MemoryBuyResult:
    prompt = f"{BUY_PROMPT}\n老人的口述是：'{speech_query}'"
    return await gemini_engine.generate_structured(prompt, None, MemoryBuyResult)
