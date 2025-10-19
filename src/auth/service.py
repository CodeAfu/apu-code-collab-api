import logging
import os
import jwt
from dotenv import load_dotenv
from typing import Annotated
from datetime import datetime, timedelta, timezone
from sqlmodel import Session
from fastapi import Depends 
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from src.entities.user import User
from src.auth.models import Token, TokenData
from src.utils import security
from src.exceptions import AuthenticationError
from src.user.models import RegisterUserRequest
from src.user.service import get_user_by_email

load_dotenv()

SECRET_KEY = os.getenv("JWT_SECRET_KEY")
ALGORITHM = os.getenv("ENCRYPTION_ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = 1 # TODO: Increase to 15
REFRESH_TOKEN_EXPIRE_DAYS = 7

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

def get_password_hash(password: str) -> str:
    return security.get_password_hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return security.verify_password(plain_password, hashed_password)


def authenticate_user(session: Session, email: str, password: str) -> User:
    user = get_user_by_email(session, email)
    if not user or not security.verify_password(password, user.password_hash):
        logging.warning(f"Failed to authenticate attempt for email: {email}")
        return False
    return user


def create_refresh_token(email: str, user_id: str, apu_id: str, expires_delta: timedelta) -> str:
    encode = {
        "id": user_id,
        "sub": email,
        "apu_id": apu_id,
        "type": "refresh",
        "exp": datetime.now(timezone.utc) + expires_delta
    }
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def create_access_token(email: str, user_id: str, apu_id: str, expires_delta: timedelta) -> str:
    encode = {
        "id": user_id,
        "sub": email,
        "apu_id": apu_id,
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
        email = payload.get("sub")
        apu_id = payload.get("apu_id")
        token_type = payload.get("type", "access")

        if token_type != expected_type:
            raise AuthenticationError()

        return TokenData(
            user_id=user_id,
            email=email,
            apu_id=apu_id,
            token_type=token_type
        )
    except jwt.PyJWTError as e:
        logging.warning(f"Token verification failed: {str(e)}")
        raise AuthenticationError()


def register_user(session: Session, request: RegisterUserRequest) -> User:
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

        return user
    except Exception as e:
        logging.error(f"Failed to register user: {request.email}. Error: {str(e)}")
        raise


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> TokenData:
    return verify_token(token)

CurrentUser = Annotated[TokenData, Depends(get_current_user)]


def login_for_access_token(
        session: Session,
        form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> Token:
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise AuthenticationError()
    
    access_token = create_access_token(
        user.email, 
        user.id, 
        user.apu_id, 
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    refresh_token = create_refresh_token(
        user.email,
        user.id,
        user.apu_id,
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    return Token(access_token=access_token, refresh_token=refresh_token, token_type='bearer')
