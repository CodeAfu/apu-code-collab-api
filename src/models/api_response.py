from pydantic import BaseModel, ConfigDict
from typing import Any, Literal

class SuccessResponse(BaseModel):
    status: int
    success: Literal[True] = True
    data: Any
    message: str | None = None

class ErrorResponse(BaseModel):
    status: int
    success: Literal[False] = False
    error: Any
    message: str | None = None

APIResponse = SuccessResponse | ErrorResponse