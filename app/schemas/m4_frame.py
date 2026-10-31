from pydantic import BaseModel, Field

class FamilyPhotoPush(BaseModel):
    image_url: str
    sender_name: str = Field(description="Sender relationship e.g., 'Daughter Xiaoyu'")
    caption: str = Field(description="Accompanying warm message")

class FramePhotoItem(BaseModel):
    id: str
    image_url: str
    caption: str
    timestamp: str
