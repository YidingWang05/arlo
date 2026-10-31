from pydantic import BaseModel
from typing import Generic, TypeVar, Optional, Literal

T = TypeVar("T")


class ResponseMeta(BaseModel):
    source: Literal["gemini", "demo", "keyword", "local", "unverified"]
    interaction_id: str | None = None
    model: str | None = None
    is_mock: bool = False


def generation_meta(metadata):
    if metadata is None:
        return ResponseMeta(source="unverified")
    return ResponseMeta(source=metadata.source, interaction_id=metadata.interaction_id,
                        model=metadata.model, is_mock=metadata.source == "demo")

class BaseResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
    meta: ResponseMeta | None = None
