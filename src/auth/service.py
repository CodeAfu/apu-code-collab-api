from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from loguru import logger
from sqlmodel import Session, select

from src.auth.models import TokenData, TokenResponse
from src.database.core import get_session
from src.config import settings
from src.entities.refresh_token import RefreshToken
from src.entities.user import User
from src.exceptions import AuthenticationError
from src.user import service as user_service
from src.utils import security

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")


def get_password_hash(password: str) -> str:
    """
    Hash a plain text password using bcrypt.

    Parameters:
        password (str): The plain text password.

    Returns:
        str: The hashed password string.
    """
    return security.get_password_hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain text password against a hashed password.

    Parameters:
        plain_password (str): The user-provided plain text password.
        hashed_password (str): The stored bcrypt hash.

    Returns:
        bool: True if they match, False otherwise.
    """
    return security.verify_password(plain_password, hashed_password)


def authenticate_user(session: Session, apu_id: str, password: str) -> User:
    """
    Verify user credentials and return the user entity if valid.

    This function includes protection against timing attacks. If the user is not found,
    it performs a dummy hash verification to ensure the response time is similar
    to a failed password check.

    Parameters:
        session (Session): The database session.
        apu_id (str): The unique APU ID (e.g., TP number).
        password (str): The plain text password.

    Returns:
        User: The authenticated user entity.

    Raises:
        AuthenticationError: If the user is not found or the password does not match.
    """
    user = user_service.get_user_by_apu_id(session, apu_id)
    if not user:
        # Constant-time dummy hash to prevent timing attacks
        security.verify_password(password, security.get_password_hash("dummy"))
        raise AuthenticationError(
            message="Invalid Email or Password",
            debug=f"User with APU ID '{apu_id}' not found",
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
    """
    Generate a JWT refresh token.

    Parameters:
        user_id (str): The database ID of the user.
        apu_id (str): The user's APU ID (subject).
        role (str): The user's role.
        expires_delta (timedelta): How long until the token expires.

    Returns:
        str: Encoded JWT string.
    """
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
    """
    Generate a JWT access token.

    Parameters:
        user_id (str): The database ID of the user.
        apu_id (str): The user's APU ID (subject).
        role (str): The user's role.
        expires_delta (timedelta): How long until the token expires.

    Returns:
        str: Encoded JWT string.
    """
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


def refresh_access_token(session: Session, old_token_str: str) -> TokenResponse:
    """
    Validate a refresh token and issue a new access token.

    This implements token rotation or validation logic. It checks if the token exists
    in the database, hasn't been revoked, and hasn't expired.

    Parameters:
        session (Session): The database session.
        old_token_str (str): The incoming refresh token string.

    Returns:
        TokenResponse: A new access token and the (potentially rotated) refresh token.

    Raises:
        AuthenticationError: If the token is invalid, revoked, expired, or missing required claims.
    """
    token_data = verify_token(old_token_str, expected_type="refresh")

    if token_data.apu_id is None:
        raise AuthenticationError(
            error_code="TOKEN_REVOKED",
            message="Refresh token is invalid or revoked",
            debug=f"Token ID missing from token: {old_token_str}",
        )

    db_token = session.exec(
        select(RefreshToken).where(
            RefreshToken.token == old_token_str,
            RefreshToken.revoked == False,  # noqa
        )
    ).first()

    if not db_token:
        raise AuthenticationError(
            error_code="TOKEN_REVOKED", message="Refresh token is invalid or revoked"
        )

    logger.info(f"Refresh token: {old_token_str}")
    logger.info(f"DB token: {db_token}")
    logger.info(f"Token match: {db_token.token == old_token_str}")

    expiry = db_token.expires_at

    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=timezone.utc)

    if db_token.expires_at < datetime.now(timezone.utc):
        raise AuthenticationError(
            error_code="TOKEN_EXPIRED", message="Refresh token has expired"
        )

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
        access_token=new_access_token, refresh_token=old_token_str, token_type="Bearer"
    )


def revoke_refresh_token(session: Session, refresh_token: str) -> None:
    """
    Revoke a refresh token, preventing its future use.

    Parameters:
        session (Session): The database session.
        refresh_token (str): The token string to revoke.

    Raises:
        AuthenticationError: If the token is not found in the database.
    """
    db_token = session.exec(
        select(RefreshToken).where(RefreshToken.token == refresh_token)
    ).first()

    if not db_token:
        logger.warning("Refresh token not found")
        raise AuthenticationError(
            error_code="TOKEN_REVOKED",
            message="Refresh token is invalid or revoked",
        )

    db_token.revoked = True
    db_token.revoked_at = datetime.now(timezone.utc)
    session.add(db_token)
    session.commit()
    logger.info("Refresh token revoked successfully")


def verify_token(token: str, expected_type: str = "access") -> TokenData:
    """
    Decode and validate a JWT token's signature, type, and payload.

    Parameters:
        token (str): The JWT string.
        expected_type (str): The expected 'type' claim (e.g., 'access' or 'refresh').

    Returns:
        TokenData: Extracted payload data (user_id, apu_id, etc.).

    Raises:
        AuthenticationError: If the token is expired, invalid, or has the wrong type/payload.
    """
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


# def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    session: Session = Depends(get_session),
) -> User:
    """
    FastAPI Dependency: Retrieve the currently authenticated user from the Bearer token.

    This validates the access token and checks if the user exists and is active.

    Parameters:
        token (str): The JWT access token (injected via OAuth2Bearer).
        session (Session): The database session.

    Returns:
        User: The active user entity associated with the token.

    Raises:
        AuthenticationError: If the user is not found or is inactive.
    """
    token_data = verify_token(token)
    user = session.get(User, token_data.user_id)

    if not user:
        raise AuthenticationError(
            message="User not found",
            error_code="USER_NOT_FOUND",
            debug=f"User with ID '{token_data.user_id}' not found",
        )

    if not user.is_active:
        raise AuthenticationError(
            message="User is not active",
            error_code="USER_NOT_ACTIVE",
            debug=f"User with ID '{token_data.user_id}' is not active",
        )

    return user


CurrentActiveUser = Annotated[User, Depends(get_current_user)]


def login_for_access_token(
    session: Session,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    """
    Perform the full login flow: authenticate user, generate tokens, and persist the refresh token.

    Parameters:
        session (Session): The database session.
        form_data (OAuth2PasswordRequestForm): Contains username and password.

    Returns:
        TokenResponse: The access token and refresh token.

    Raises:
        AuthenticationError: If credentials are invalid or token persistence fails.
    """
    user = authenticate_user(session, form_data.username, form_data.password)

    access_token = create_access_token(
        user_id=user.id,
        apu_id=user.apu_id,
        role=user.role,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    refresh_token = create_refresh_token(
        user_id=user.id,
        apu_id=user.apu_id,
        role=user.role,
        expires_delta=timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    try:
        db_refresh_token = RefreshToken(
            token=refresh_token,
            user_id=user.id,
            expires_at=datetime.now(timezone.utc)
            + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            revoked=False,
        )
        session.add(db_refresh_token)
        session.commit()
        session.refresh(db_refresh_token)
        return TokenResponse(
            access_token=access_token, refresh_token=refresh_token, token_type="Bearer"
        )
    except Exception as e:
        logger.error(f"Error creating refresh token: {str(e)}")
        raise AuthenticationError(
            message="Error creating refresh token",
            error_code="REFRESH_TOKEN_CREATION_FAILED",
            debug=str(e),
        )
