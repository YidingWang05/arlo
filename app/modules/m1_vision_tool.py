from app.schemas.m1_vision import VisionExplainResult
from app.core.base_model import gemini_engine

SYSTEM_PROMPT = """
你是一名精通适老化沟通的家庭医生与生活助手。
面对老人拍摄的药品盒、说明书或账单：
1. 忽略复杂的化学分子式与冗长套话。
2. 提取最核心信息（用法、剂量、频次或缴费金额）。
3. headline_large 必须控制在15个字以内，适合视力退化的老人一眼看清。
4. audio_script 必须使用口语化、温暖的大白话，适合朗读。
"""

async def run_vision_explain(image_bytes: bytes, user_query: str) -> VisionExplainResult:
    prompt = f"{SYSTEM_PROMPT}\n老人的提问是：{user_query}"
    return await gemini_engine.generate_structured(prompt, image_bytes, VisionExplainResult)
