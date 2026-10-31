from pydantic import BaseModel, Field, ConfigDict, model_validator
from typing import List

class CandidateItem(BaseModel):
    item_id: str
    name: str
    image_url: str
    display_tag: str = Field(description="Single-decision label e.g., 'Left option (daughter bought before)'")

class MemoryBuyRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    speech_query: str = Field(min_length=1, max_length=1000, description="Spoken household product query")

class MemoryBuyResult(BaseModel):
    spoken_prompt: str = Field(description="Question asked by the frame e.g., 'Is it the round blue bottle on the left?'")
    candidates: List[CandidateItem] = Field(min_length=2, max_length=2, description="Exactly two candidate cards, ordered A then B")

    @model_validator(mode="after")
    def distinct_candidates(self):
        if self.candidates[0].item_id == self.candidates[1].item_id:
            raise ValueError("Candidates must be different items")
        return self
