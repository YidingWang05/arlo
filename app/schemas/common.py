from pydantic import BaseModel
from typing import Generic, TypeVar, Optional

T = TypeVar("T")

class BaseResponse(BaseModel, Generic[T]):
    code: int = 200
    message: str = "success"
    data: Optional[T] = None
