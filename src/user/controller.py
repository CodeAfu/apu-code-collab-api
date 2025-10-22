from dotenv import load_dotenv
from fastapi import status, APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session

from src.api_response import SuccessResponse
from src.user import service
from src.exceptions import InternalException
from src.user.models import CreateUserRequest
from src.entities.user import User
from src.database.core import get_session
from src.config import settings

load_dotenv()

user_router = APIRouter(prefix="/api/v1/users",)
unknown_error_message = "Unknown error occurred"


@user_router.get(
    "/",
    response_model=list[User],
    response_model_exclude_none=True,
)
async def get_users(session: Session = Depends(get_session)) -> JSONResponse:
    # TODO: Protect this better
    if not settings.is_development:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Invalid Permission",
                "message": "You are not allowed to accesss this endpoint",
            }
        )
    
    try:
        users = service.get_users(session)
        return users
    except HTTPException:
        raise
    except Exception as e:
        raise InternalException(
            message=unknown_error_message,
            error=str(e)
        )


@user_router.get(
    "/{user_id}",
    response_model=User,
    response_model_exclude_none=True,
)
# @limiter.limit("1/second")
async def get_user(user_id: str, session: Session = Depends(get_session)) -> JSONResponse:
    try:
        user = service.get_user(session, user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User does not exist"
            )
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise InternalException(
            message=unknown_error_message,
            error=str(e)
        )
 

@user_router.post(
    "",
    response_model=User,
    response_model_exclude_none=True,
)
async def create_user(
    request: CreateUserRequest,
    session: Session = Depends(get_session)
) -> JSONResponse:
    try:
        email_is_unique = service.is_unique_user(session, request.email, request.apu_id)
        if not email_is_unique:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "Email or TP number is already registered",
                    "message": "User is already registered",
                }
            )
        
        user = service.create_user(session, request);
        return user
    except HTTPException:
        raise
    except Exception as e:
        raise InternalException(
            message=unknown_error_message,
            error=str(e)
        )


@user_router.delete(
    "/{user_id}",
    response_model=dict,
    response_model_exclude_none=False,
)
async def delete_user(user_id: str, session: Session = Depends(get_session)):
    try:
        deleted = service.delete_user(session, user_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "USER_NOT_FOUND",
                    "message": "User does not exist"
                }
            )
        
        return { "message": "User deleted successfully" }
    except HTTPException:
        raise
    except Exception as e:
        raise InternalException(
            message=unknown_error_message,
            error=str(e)
        )

