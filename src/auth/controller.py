from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from loguru import logger
from sqlmodel import Session

from src.auth import service as auth_service
from src.auth.models import Token
from src.config import settings
from src.database.core import get_session
from src.entities.user import UserRole
from src.rate_limiter import limiter
from src.user import service as user_service
from src.user.models import CreateUserRequest, CreateUserResponse, RegisterUserRequest

auth_router = APIRouter(prefix="/api/v1/auth")


@auth_router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=CreateUserResponse,
)
@limiter.limit("5/hour")
async def register_user(
    request: Request,
    register_user_request: RegisterUserRequest,
    session: Session = Depends(get_session),
):
    """
    Register a new student account.

    This endpoint handles public registration. It enforces specific rate limits
    to prevent spam and defaults the new user's role to 'STUDENT'.

    Parameters:
        register_user_request (RegisterUserRequest): Payload containing registration details.
        session (Session): The database session dependency.

    Returns:
        CreateUserResponse: The newly created user's public profile.
    """
    logger.info(f"Register user: {register_user_request.apu_id}")
    create_user_request = CreateUserRequest(
        id=register_user_request.apu_id,
        first_name=register_user_request.first_name,
        last_name=register_user_request.last_name,
        apu_id=register_user_request.apu_id,
        email=register_user_request.email,
        password=register_user_request.password,
        role=UserRole.STUDENT,
        is_active=True,
        github_id=None,
        github_username=None,
        github_access_token=None,
        github_avatar_url=None,
    )
    return user_service.create_user(session, create_user_request)


@auth_router.post("/token", response_model=Token)
@limiter.limit("10/minute")
async def login_for_access_token(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(get_session),
):
    """
    Authenticate a user and issue access/refresh tokens.

    This endpoint implements the OAuth2 Password Grant flow. On success, it returns
    a short-lived Access Token in the response body and sets a long-lived HTTP-only
    Refresh Token cookie.

    Parameters:
        form_data (OAuth2PasswordRequestForm): The standard OAuth2 form containing 'username' and 'password'.
        response (Response): The FastAPI response object (used to set cookies).
        session (Session): The database session dependency.

    Returns:
        Token: The JWT access token and token type.
    """
    logger.info(f"Logging in for access token: {form_data.username}")
    token = auth_service.login_for_access_token(session, form_data)
    response.set_cookie(
        key="refresh_token",
        value=token.refresh_token,
        httponly=True,
        secure=True if settings.is_production else False,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite="lax",
    )
    logger.info(f"Logged in for access token: {token.access_token}")
    return token


@auth_router.post("/logout", status_code=status.HTTP_200_OK)
@limiter.limit("10/minute")
async def logout(
    request: Request,
    response: Response,
    refresh_token: str = Cookie(None),
    session: Session = Depends(get_session),
):
    """
    Log out the user by revoking their refresh token.

    This invalidates the provided refresh token in the database and clears the
    HTTP-only cookie from the client's browser.

    Parameters:
        response (Response): The FastAPI response object (used to delete cookies).
        refresh_token (str): The refresh token retrieved from the 'refresh_token' cookie.
        session (Session): The database session dependency.

    Returns:
        dict: A success message indicating the user is logged out.
    """
    if refresh_token:
        auth_service.revoke_refresh_token(session, refresh_token)

    response.delete_cookie(
        key="refresh_token",
        httponly=True,
        secure=True if settings.is_production else False,
        samesite="lax",
    )

    return {"message": "Logged out successfully"}


@auth_router.post("/refresh", response_model=Token)
@limiter.limit("60/hour")
async def refresh_access_token(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
    refresh_token: str = Cookie(None),
):
    """
    Exchange a valid Refresh Token for a new Access Token.

    This allows the frontend to maintain a seamless session without re-entering credentials.
    The old refresh token is consumed and replaced with a new one (token rotation).

    Parameters:
        response (Response): The FastAPI response object (used to update cookies).
        refresh_token (str): The existing refresh token from the cookie.
        session (Session): The database session dependency.

    Returns:
        Token: A new JWT access token.

    Raises:
        AuthenticationError: If the refresh token is missing, expired, or invalid.
    """
    if not refresh_token:
        logger.error("Missing refresh token")
        raise auth_service.AuthenticationError(
            message="Missing refresh token", error_code="REFRESH_TOKEN_MISSING"
        )
    logger.info("Refreshing access token")
    token = auth_service.refresh_access_token(session, refresh_token)
    response.set_cookie(
        key="refresh_token",
        value=token.refresh_token,
        httponly=True,
        secure=True if settings.is_production else False,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite="lax",
    )
    logger.info("Token refreshed successfully")
    return token
