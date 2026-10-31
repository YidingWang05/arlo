from pydantic import BaseModel, Field

class FamilyPhotoPush(BaseModel):
    image_url: str
    sender_name: str = Field(description="家属称谓，如'大女儿小雨'")
    caption: str = Field(description="家属留言附言")

class FramePhotoItem(BaseModel):
    id: str
    image_url: str
    caption: str
    timestamp: str
