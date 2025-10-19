from pydantic import BaseModel
from typing import Generic, Literal, TypeVar

T = TypeVar('T')
E = TypeVar('E')

class SuccessResponse(BaseModel, Generic[T]):
    success: Literal[True] = True
    data: T
    message: str | None = None

class ErrorResponse(BaseModel, Generic[E]):
    success: Literal[False] = False
    error: E
    message: str | None = None

APIResponse = SuccessResponse | ErrorResponse