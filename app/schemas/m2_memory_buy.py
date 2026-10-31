from pydantic import BaseModel, Field
from typing import List

class CandidateItem(BaseModel):
    item_id: str
    name: str
    image_url: str
    display_tag: str = Field(description="单决策大标签，如'左边这个 (女儿买过)'")

class MemoryBuyRequest(BaseModel):
    speech_query: str = Field(description="老人口述，如'买上次小雨买的蓝色洗洁精'")

class MemoryBuyResult(BaseModel):
    spoken_prompt: str = Field(description="相框提问话术，如'张爷爷，是左边这个圆瓶的吗？'")
    candidates: List[CandidateItem] = Field(description="固定返回 2 张大图供二选一")
