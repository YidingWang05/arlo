from pydantic import BaseModel, Field
from typing import List

class VisionExplainResult(BaseModel):
    category: str = Field(default="MEDICINE", description="类别：MEDICINE, BILL, NOTICE, OTHER")
    headline_large: str = Field(description="大字号核心结论，<=15字，如'早晚各1粒 · 饭后温水服'")
    audio_script: str = Field(description="用于 TTS 播报的大白话温和解释")
    action_items: List[str] = Field(default_factory=list, description="要点清单")
    is_blurry: bool = Field(default=False, description="是否因反光/手抖需要重新拍摄")
