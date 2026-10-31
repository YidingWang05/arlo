from pydantic import BaseModel, Field
from typing import List

class CandidateItem(BaseModel):
    item_id: str
    name: str
    image_url: str
    display_tag: str = Field(description="Single-decision label e.g., 'Left option (daughter bought before)'")

class MemoryBuyRequest(BaseModel):
    speech_query: str = Field(description="Elderly voice query e.g., 'Buy the blue bottle detergent my daughter bought'")

class MemoryBuyResult(BaseModel):
    spoken_prompt: str = Field(description="Question asked by the frame e.g., 'Is it the round blue bottle on the left?'")
    candidates: List[CandidateItem] = Field(description="Exactly two high-res candidate images for binary visual confirmation")
