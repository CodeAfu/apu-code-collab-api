from sqlmodel import Session, select

from src.models.user import CreateUserRequest, User


def get_users(session: Session) -> list[User]:
    return session.exec(select(User)).all()


def get_user(session: Session, user_id: str) -> User:
    return session.exec(
        select(User).where(User.id == user_id)
    ).first()


def is_unique_email(session: Session, email) -> bool:
    return session.exec(
        select(User).where((User.email == email))
    ).first() is None


def create_user(session: Session, request: CreateUserRequest) -> User:
    user = User(
        name=request.name,
        email=request.email,
        student_id=request.student_id,
        role=request.role,
        is_active=request.is_active
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


