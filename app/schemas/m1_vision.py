from pydantic import BaseModel, Field
from typing import List

class VisionExplainResult(BaseModel):
    category: str = Field(default="MEDICINE", description="Detected category: MEDICINE, BILL, NOTICE, OTHER")
    headline_large: str = Field(description="Large-print core takeaway under 15 words for older adults")
    audio_script: str = Field(description="Warm, conversational spoken text suitable for TTS playback")
    action_items: List[str] = Field(default_factory=list, description="Key actionable checklist items")
    is_blurry: bool = Field(default=False, description="Flag indicating poor visibility, glare, or motion blur")
