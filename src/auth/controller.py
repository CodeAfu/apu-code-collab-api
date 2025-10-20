from typing import Annotated
from fastapi import APIRouter, Depends, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlmodel import Session

from src.api_response import SuccessResponse
from src.auth.models import RefreshTokenRequest, Token
from src.auth import service
from src.database.core import get_session
from src.rate_limiter import limiter
from src.user.models import CreateUserRequest

auth_router = APIRouter(prefix="/api/v1/auth")


@auth_router.post("/")
@limiter.limit("5/hour")
async def register_user(request: Request, register_user_request: CreateUserRequest, session: Session = Depends(get_session)):
    user = service.register_user(session, register_user_request)
    return SuccessResponse(
        data=user,
        message="User has been successfully registered"
    )


@auth_router.post(
    "/token",
    response_model=Token
)
async def login_for_access_token(
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
        session: Session = Depends(get_session)
):
    return service.login_for_access_token(session, form_data)


@auth_router.post("/refresh", response_model=Token)
async def refresh_access_token(
    refresh_token_request: RefreshTokenRequest,
    session: Session = Depends(get_session)
):
    return service.refresh_access_token(session, refresh_token_request.refresh_token)