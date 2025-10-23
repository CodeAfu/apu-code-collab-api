from fastapi import HTTPException, status
from src.config import settings


class InternalException(HTTPException):
    def __init__(
            self,
            message: str = "An unexpected error occurred",
            error: str | None = None,
            status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        detail = { "message": message }
        if error and settings.is_development:
            detail["error"] = error

        super().__init__(
            status_code=status_code,
            detail=detail
        )

class UserDoesNotExistException(HTTPException):
    def __init__(
        self,
        message: str = "User does not exist",
        error: str | None = None,
        status_code: int = status.HTTP_404_NOT_FOUND,
    ):
        detail = { "message": message }
        if error and settings.is_development:
            detail["error"] = error

        super().__init__(
            status_code=status_code,
            detail=detail
        )

class UserAlreadyExistsException(HTTPException):
    def __init__(
        self,
        message: str = "Email or ID already exists",
        error: str | None = None,
        status_code: int = status.HTTP_409_CONFLICT,
    ):
        detail = { "message": message }
        if error and settings.is_development:
            detail["error"] = error

        super().__init__(
            status_code=status_code,
            detail=detail
        )

class AuthenticationError(HTTPException):
    def __init__(
            self,
            message: str = "Could not validate user",
            error_code: str = "AUTHENTICATION_FAILED",
            debug: str | None = None,
            status_code: int = status.HTTP_401_UNAUTHORIZED,
    ):
        detail = {"message": message, "error_code": error_code}
        if debug and settings.is_development:
            detail["debug"] = debug

        super().__init__(
            status_code=status_code,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )
