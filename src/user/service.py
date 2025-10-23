from sqlmodel import Session, select

from src.exceptions import UserAlreadyExistsException, UserDoesNotExistException
from src.entities.user import User
from src.user.models import CreateUserRequest
from src.utils import security


def get_users(session: Session) -> list[User]:
    return session.exec(select(User)).all()


def get_user(session: Session, user_id: str) -> User:
    user = session.exec(
        select(User).where(User.id == user_id)
    ).first()

    if not user:
        raise UserDoesNotExistException()
    
    return user


def get_user_by_email(session: Session, email: str) -> User:
    return session.exec(
        select(User).where(User.email == email)
    ).first()


def is_unique_email(session: Session, email: str) -> bool:
    return session.exec(
        select(User).where((User.email == email))
    ).first() is None


def ensure_user_is_unique(session: Session, email: str, apu_id: str) -> None:
    user = session.exec(
        select(User).where((User.email == email) | (User.apu_id == apu_id))
    ).first()

    if user:
        raise UserAlreadyExistsException()


def create_user(session: Session, request: CreateUserRequest) -> User:
    password_hash = None
    if request.password:
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


def delete_user(session: Session, user_id: str) -> User:
    user = session.exec(
        select(User).where(User.id == user_id)
    ).first()
    
    if not user:
        raise UserDoesNotExistException()
    
    session.delete(user)
    session.commit()

    return user
