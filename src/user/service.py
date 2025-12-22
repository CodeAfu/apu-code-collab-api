from typing import Sequence

from sqlmodel import Session, select
from loguru import logger
from sqlalchemy.exc import IntegrityError

from src.entities.user import User
from src.exceptions import UserAlreadyExistsException, UserDoesNotExistException
from src.user.models import CreateUserRequest
from src.utils import security
from src.exceptions import ConflictException, InternalException


def get_users(session: Session) -> Sequence[User]:
    return session.exec(select(User)).all()


def get_user(session: Session, user_id: str) -> User:
    user = session.exec(select(User).where(User.id == user_id)).first()

    if not user:
        raise UserDoesNotExistException()

    return user


def get_user_by_email(session: Session, email: str) -> User | None:
    return session.exec(select(User).where(User.email == email)).first()


def get_user_by_apu_id(session: Session, apu_id: str) -> User | None:
    return session.exec(select(User).where(User.apu_id == apu_id)).first()


def is_unique_email(session: Session, email: str) -> bool:
    return session.exec(select(User).where((User.email == email))).first() is None


def is_unique_apu_id(session: Session, apu_id: str) -> bool:
    return session.exec(select(User).where((User.apu_id == apu_id))).first() is None


def ensure_user_is_unique(session: Session, email: str | None, apu_id: str) -> None:
    conditions = [User.apu_id == apu_id]

    if email is not None:
        conditions.append(User.email == email)

    statement = select(User).where(*conditions)

    user = session.exec(statement).first()

    if user:
        raise UserAlreadyExistsException()


def create_user(session: Session, request: CreateUserRequest) -> User:
    try:
        password_hash = security.get_password_hash(request.password)

        logger.debug(f"Password hash: {password_hash}")
        logger.info(f"Creating user: {request.apu_id}")

        user = User(
            first_name=request.first_name,
            last_name=request.last_name,
            apu_id=request.apu_id,
            email=request.email,
            password_hash=password_hash,
            role=request.role,
            github_id=request.github_id,
            github_username=request.github_username,
            github_access_token=request.github_access_token,
            github_avatar_url=request.github_avatar_url,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except IntegrityError as e:
        session.rollback()
        if "unique constraint" in str(e).lower():
            logger.error(f"Email already registered: {request.email}")
            raise ConflictException("Email already registered")
        logger.exception(f"Failed to register user: {request.apu_id}")
        raise
    except Exception:
        session.rollback()
        logger.exception(f"Failed to register user: {request.apu_id}")
        raise InternalException("Failed to create user")


def delete_user(session: Session, user_id: str) -> User:
    user = session.exec(select(User).where(User.id == user_id)).first()

    if not user:
        raise UserDoesNotExistException()

    session.delete(user)
    session.commit()

    return user
