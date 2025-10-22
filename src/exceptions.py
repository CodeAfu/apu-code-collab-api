from fastapi import HTTPException, status
from src.config import settings


class InternalException(HTTPException):
    def __init__(
            self,
            message: str = "An unexpected error occurred",
            error: str | None = None
    ):
        detail = { "message": message }
        if error and settings.is_development:
            detail["error"] = error

        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )

class AuthenticationError(HTTPException):
    def __init__(
            self,
            message: str = "Could not validate user",
            error: str = "AUTHENTICATON FAILED"
    ):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={ "message": message, "error": error }
        )
