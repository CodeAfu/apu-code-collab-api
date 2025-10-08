from fastapi import Depends
from sqlmodel import Session, select

from src.models.user import CreateUserRequest, User
from src.utils.db import get_session


class UserService:
    def __init__(self, session: Session):
        self.session = session
    
    def get_users(self) -> list[User]:
        return self.session.exec(select(User)).all()
    
    def get_user(self, user_id: str) -> User:
        return self.session.exec(
            select(User).where(User.id == user_id)
        ).first()
    
    def is_unique_email(self, email) -> bool:
        return self.session.exec(
            select(User).where((User.email == email))
        ).first() is None

    def create_user(self, request: CreateUserRequest) -> User:
        user = User(
            name=request.name,
            email=request.email,
            student_id=request.student_id,
            role=request.role,
            is_active=request.is_active
        )

        self.session.add(user)
        self.session.commit()
        self.session.refresh(user)

        return user
    
    def delete_user(self, user_id: str) -> bool:
        user = self.session.exec(
            select(User).where(User.id == user_id)
        ).first()
        
        if not user:
            return False
        
        self.session.delete(user)
        self.session.commit()
        return True


def get_user_service(session: Session = Depends(get_session)) -> UserService:
    return UserService(session)
