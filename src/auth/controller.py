from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from src.auth import service
from src.auth.models import Token
from src.config import settings
from src.database.core import get_session
from src.rate_limiter import limiter
from src.user.models import CreateUserRequest

auth_router = APIRouter(prefix="/api/v1/auth")


@auth_router.post(
    "/register",
    status_code=status.HTTP_201_CREATED,
    response_model=bool,
)
@limiter.limit("5/hour")
async def register_user(
    request: Request,
    register_user_request: CreateUserRequest,
    session: Session = Depends(get_session),
):
    return service.register_user(session, register_user_request)


@auth_router.post("/token", response_model=Token)
@limiter.limit("10/minute")
async def login_for_access_token(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    session: Session = Depends(get_session),
):
    token = service.login_for_access_token(session, form_data)
    response.set_cookie(
        key="refresh_token",
        value=token.refresh_token,
        httponly=True,
        secure=True,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
        samesite="lax",
    )
    return token


@auth_router.post("/refresh", response_model=Token)
@limiter.limit("20/hour")
async def refresh_access_token(
    request: Request,
    response: Response,
    session: Session = Depends(get_session),
    refresh_token: str = Cookie(None),
):
    if not refresh_token:
        raise service.AuthenticationError(
            message="Missing refresh token", error_code="REFRESH_TOKEN_MISSING"
        )

    token = service.refresh_access_token(session, refresh_token)
    response.set_cookie(
        key="refresh_token",
        value=token.access_token,
        httponly=True,
        secure=True,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        samesite="lax",
    )
    return token
