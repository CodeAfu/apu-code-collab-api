from sqlmodel import Session, select

from src.entities.user import User
from src.user.models import CreateUserRequest
from src.utils import security


def get_users(session: Session) -> list[User]:
    return session.exec(select(User)).all()


def get_user(session: Session, user_id: str) -> User:
    return session.exec(
        select(User).where(User.id == user_id)
    ).first()


def get_user_by_email(session: Session, email: str) -> User:
    return session.exec(
        select(User).where(User.email == email)
    ).first()


def is_unique_email(session: Session, email: str) -> bool:
    return session.exec(
        select(User).where((User.email == email))
    ).first() is None


def is_unique_user(session: Session, email: str, apu_id: str) -> bool:
    return session.exec(
        select(User).where((User.email == email) | (User.apu_id == apu_id))
    ).first() is None


def create_user(session: Session, request: CreateUserRequest) -> User:
    print(f"Raw Password: {request.password}")
    password_hash = security.get_password_hash(request.password)
    print(f"Hashed Password: {password_hash}")
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


def delete_user(session: Session, user_id: str) -> bool:
    user = session.exec(
        select(User).where(User.id == user_id)
    ).first()
    
    if not user:
        return False
    
    session.delete(user)
    session.commit()
    return True
