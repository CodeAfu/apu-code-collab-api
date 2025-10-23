import logging
import jwt
from typing import Annotated
from datetime import datetime, timedelta, timezone
from sqlmodel import Session
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError

from src.entities.user import User
from src.auth.models import Token, TokenData
from src.utils import security
from src.exceptions import AuthenticationError, ConflictException, InternalException
from src.user.models import CreateUserRequest
from src.user.service import get_user_by_email
from src.config import settings

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.ENCRYPTION_ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = 1 # TODO: Increase to 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

def get_password_hash(password: str) -> str:
    return security.get_password_hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return security.verify_password(plain_password, hashed_password)


def authenticate_user(session: Session, email: str, password: str) -> User:
    user = get_user_by_email(session, email)
    if not user:
        # Constant-time dummy hash to prevent timing attacks
        security.verify_password(password, security.get_password_hash("dummy"))
        raise AuthenticationError(
            message="Invalid Email or Password",
            debug=f"User with email '{email}' not found"
        )
    
    if not security.verify_password(password, user.password_hash):
        raise AuthenticationError(
            message="Invalid Email or Password",
            debug=f"Password entry '{password}' does not match the password hash"
        )
    
    return user


def create_refresh_token(email: str, user_id: str, apu_id: str, role: str, expires_delta: timedelta) -> str:
    encode = {
        "id": user_id,
        "sub": email,
        "apu_id": apu_id,
        "role": role,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + expires_delta
    }
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(email: str, user_id: str, apu_id: str, role: str, expires_delta: timedelta) -> str:
    encode = {
        "id": user_id,
        "sub": email,
        "apu_id": apu_id,
        "role": role,
        "type": "access",
        "exp": datetime.now(timezone.utc) + expires_delta
    }
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def refresh_access_token(session: Session, refresh_token: str) -> Token:
    token_data = verify_token(refresh_token, expected_type="refresh")
    user = get_user_by_email(session, token_data.email)
    
    if not user:
        raise AuthenticationError()
    
    new_access_token = create_access_token(
        user.email,
        user.id,
        user.apu_id,
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return Token(
        access_token=new_access_token,
        refresh_token=refresh_token,  # Reuse the same refresh token
        token_type='bearer'
    )


def verify_token(token: str, expected_type: str = "access") -> TokenData:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("id")
        apu_id = payload.get("apu_id")
        email = payload.get("sub")
        token_type = payload.get("type", "access")

        if not all([user_id, email, apu_id]):
            raise AuthenticationError(
                error_code="INVALID_TOKEN",
                message="Invalid token payload",
            )

        if token_type != expected_type:
            raise AuthenticationError(
                error_code="INVALID_TOKEN_TYPE",
                message=f"Expected {expected_type} token, got {token_type}"
            )

        return TokenData(
            user_id=user_id,
            email=email,
            apu_id=apu_id,
            token_type=token_type
        )
    except jwt.ExpiredSignatureError as e:
        raise AuthenticationError(
            message="Token has expired",
            error_code="TOKEN_EXPIRED",
            debug=str(e)
        )
    except jwt.InvalidTokenError as e:
        logging.warning(f"Invalid token: {str(e)}")
        raise AuthenticationError(
            message="Invalid token",
            error_code="INVALID_TOKEN",
            debug=str(e)
        )
    except Exception as e:
        logging.error(f"Unexpected error verifying token: {str(e)}")
        raise AuthenticationError(
            message="Token verification failed",
            error_code="TOKEN_VERIFICATION_FAILED",
            debug=str(e)
        )


def register_user(session: Session, request: CreateUserRequest) -> bool:
    try:
        password_hash = security.get_password_hash(request.password)
        user = User(
            first_name=request.first_name,
            last_name=request.last_name,
            apu_id=request.apu_id,
            email=request.email,
            password_hash=password_hash,
            role=request.role,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        return True
    except IntegrityError as e:
        session.rollback()
        if "unique constraint" in str(e).lower():
            raise ConflictException("Email already registered")
        raise
    except Exception as e:
        session.rollback()
        logging.exception(f"Failed to register user: {request.email}")
        raise InternalException("Failed to create user")
    

# def get_current_user(token: str = Depends(oauth2_scheme)) -> TokenData:
def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenData:
    return verify_token(token)

CurrentUser = Annotated[TokenData, Depends(get_current_user)]


def login_for_access_token(
    session: Session,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    user = authenticate_user(session, form_data.username, form_data.password)
    
    access_token = create_access_token(
        user.email, 
        user.id, 
        user.apu_id,
        user.role,
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    refresh_token = create_refresh_token(
        user.email,
        user.id,
        user.apu_id,
        user.role,
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    return Token(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
