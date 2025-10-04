import os
from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

from src.models.api_response import APIResponse, ErrorResponse, SuccessResponse
from src.models.user import CreateUserRequest, User
from src.utils.db import get_session

load_dotenv()
env = os.getenv("PYTHON_ENV")

user_router = APIRouter(
    prefix="/api/users"
)

@user_router.get("/")
async def get_users(session: Session = Depends(get_session)) -> APIResponse:
    if env != "development":
        return ErrorResponse(
            status=500,
            error="Invalid Permission",
            message="You do not have permissions to access this endpoint",
        )

    # TODO: Add proper role validation
    
    try:
        users = session.exec(select(User)).all()
        
        return SuccessResponse(
            status=200,
            data=[user.model_dump(exclude_none=True) for user in users],
            message="Users retrieved successfully"
        )
    except Exception as e:
        return ErrorResponse(
            status=500,
            error=str(e),
            message="Failed to retrieve users"
        )


@user_router.get("/{user_id}", response_model_exclude_none=True)
# @limiter.limit("1/second")
async def get_user(user_id: str, session: Session = Depends(get_session)) -> APIResponse:
    try:
        user = session.exec(
            select(User).where(User.id == user_id)
        ).first()

        if not user:
            return ErrorResponse(
                status=400,
                error="User does not exist",
                message="User does not exist"
            )
        
        return SuccessResponse(
            status=200,
            data=user.model_dump(exclude_none=True),
        )
    except Exception as e:
        return ErrorResponse(
            status=500,
            message="Internal Error",
            error=str(e)
        )


@user_router.post("", response_model_exclude_none=True)
async def create_user(request: CreateUserRequest, session: Session = Depends(get_session)) -> APIResponse:
    try:
        existing_user = session.exec(
            select(User).where((User.email == request.email))
        ).first()

        if existing_user:
            return ErrorResponse(
                status=409,
                error="Email or name already exists",
                message="Email or name already exists",
            )
        
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

        return SuccessResponse(
            status=201,
            data=user.model_dump(exclude_none=True),
            message="User created successfully"
        )
    except Exception as e:
        return ErrorResponse(
            status=500,
            message="Failed to create user",
            error=str(e)
        )

