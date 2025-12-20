from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Session
from loguru import logger

from src.auth.models import TokenData, TokenResponse
from src.config import settings
from src.entities.user import User, UserRole
from src.exceptions import AuthenticationError
from src.user.models import RegisterUserRequest, CreateUserResponse, CreateUserRequest
from src.user import service as user_service
from src.utils import security

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_password_hash(password: str) -> str:
    return security.get_password_hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return security.verify_password(plain_password, hashed_password)


def authenticate_user(session: Session, email: str, password: str) -> User:
    user = user_service.get_user_by_email(session, email)
    if not user:
        # Constant-time dummy hash to prevent timing attacks
        security.verify_password(password, security.get_password_hash("dummy"))
        raise AuthenticationError(
            message="Invalid Email or Password",
            debug=f"User with email '{email}' not found",
        )

    if not security.verify_password(password, user.password_hash):
        raise AuthenticationError(
            message="Invalid Email or Password",
            debug=f"Password entry '{password}' does not match the password hash",
        )

    return user


def create_refresh_token(
    user_id: str, apu_id: str, role: str, expires_delta: timedelta
) -> str:
    encode = {
        "id": user_id,
        "sub": apu_id,
        "role": role,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(
        encode, settings.JWT_SECRET_KEY, algorithm=settings.ENCRYPTION_ALGORITHM
    )


def create_access_token(
    user_id: str, apu_id: str, role: str, expires_delta: timedelta
) -> str:
    encode = {
        "id": user_id,
        "sub": apu_id,
        "role": role,
        "type": "access",
        "exp": datetime.now(timezone.utc) + expires_delta,
    }
    return jwt.encode(
        encode, settings.JWT_SECRET_KEY, algorithm=settings.ENCRYPTION_ALGORITHM
    )


def refresh_access_token(session: Session, refresh_token: str) -> TokenResponse:
    token_data = verify_token(refresh_token, expected_type="refresh")

    if token_data.apu_id is None:
        raise AuthenticationError()

    user = user_service.get_user_by_apu_id(session, token_data.apu_id)

    if not user:
        raise AuthenticationError()

    new_access_token = create_access_token(
        user.id,
        user.apu_id,
        user.role,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return TokenResponse(
        access_token=new_access_token,
        refresh_token=refresh_token,  # Reuse the same refresh token
        token_type="bearer",
    )


def verify_token(token: str, expected_type: str = "access") -> TokenData:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.ENCRYPTION_ALGORITHM]
        )
        user_id = payload.get("id")
        apu_id = payload.get("sub")
        token_type = payload.get("type", "access")

        if not all([user_id, apu_id]):
            raise AuthenticationError(
                error_code="INVALID_TOKEN",
                message="Invalid token payload",
            )

        if token_type != expected_type:
            raise AuthenticationError(
                error_code="INVALID_TOKEN_TYPE",
                message=f"Expected {expected_type} token, got {token_type}",
            )

        return TokenData(user_id=user_id, apu_id=apu_id, token_type=token_type)
    except jwt.ExpiredSignatureError as e:
        raise AuthenticationError(
            message="Token has expired", error_code="TOKEN_EXPIRED", debug=str(e)
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {str(e)}")
        raise AuthenticationError(
            message="Invalid token", error_code="INVALID_TOKEN", debug=str(e)
        )
    except Exception as e:
        logger.error(f"Unexpected error verifying token: {str(e)}")
        raise AuthenticationError(
            message="Token verification failed",
            error_code="TOKEN_VERIFICATION_FAILED",
            debug=str(e),
        )


def register_user(session: Session, request: RegisterUserRequest) -> CreateUserResponse:
    create_user_request = CreateUserRequest(
        id=request.apu_id,
        first_name=request.first_name,
        last_name=request.last_name,
        apu_id=request.apu_id,
        email=request.email,
        password=request.password,
        role=UserRole.STUDENT,
        is_active=True,
        github_id=None,
        github_username=None,
        github_access_token=None,
        github_avatar_url=None,
    )
    return user_service.create_user(session, create_user_request)


# def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenData:
    return verify_token(token)


CurrentUser = Annotated[TokenData, Depends(get_current_user)]


def login_for_access_token(
    session: Session,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    user = authenticate_user(session, form_data.username, form_data.password)

    access_token = create_access_token(
        user.apu_id,
        user.id,
        user.role,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    refresh_token = create_refresh_token(
        user.apu_id,
        user.id,
        user.role,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    return TokenResponse(
        access_token=access_token, refresh_token=refresh_token, token_type="bearer"
    )
