import os
from dotenv import load_dotenv
from fastapi import status, APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session

from src.api_response import ErrorResponse, SuccessResponse
from src.user import service
from src.exceptions import APIException
from src.user.models import CreateUserRequest
from src.entities.user import User
from src.database.core import get_session

load_dotenv()

env = os.getenv("PYTHON_ENV")

user_router = APIRouter(prefix="/api/v1/users",)


@user_router.get(
    "/",
    response_model=SuccessResponse[list[User]],
    response_model_exclude_none=True,
    responses={
        403: {"model": ErrorResponse[str]},
        500: {"model": ErrorResponse[str]}
    }
)
async def get_users(session: Session = Depends(get_session)) -> JSONResponse:
    # TODO: Protect this better
    if env != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Invalid Permission",
                "message": "You are not allowed to accesss this endpoint",
            }
        )
    
    try:
        users = service.get_users(session)
        
        return SuccessResponse(
            data=users,
            message="Users retrieved successfully"
        )
    except Exception as e:
        raise APIException(
            error=str(e),
            message="Unknown error occurred"
        )


@user_router.get(
    "/{user_id}",
    response_model=SuccessResponse[User],
    response_model_exclude_none=True,
    responses={
        404: {"model": ErrorResponse[str]},
        500: {"model": ErrorResponse[str]}
    }
)
# @limiter.limit("1/second")
async def get_user(user_id: str, session: Session = Depends(get_session)) -> JSONResponse:
    try:
        user = service.get_user(session, user_id)
        if not user:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                error="User does not exist",
                message="User does not exist"
            )
        
        return SuccessResponse(
            data=user,
            message="User retrieved successfully",
        )
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            error=str(e),
            message="Unknown error occurred"
        )
 

@user_router.post(
    "",
    response_model=SuccessResponse[User],
    response_model_exclude_none=True,
    responses={
        409: {"model": ErrorResponse[str]},
        500: {"model": ErrorResponse[str]},
    }
)
async def create_user(
        request: CreateUserRequest,
        session: Session = Depends(get_session)
) -> JSONResponse:
    try:
        email_is_unique = service.is_unique_user(session, request.email, request.apu_id)
        if not email_is_unique:
            raise APIException(
                status_code=status.HTTP_409_CONFLICT,
                error= "Email or TP number is already registered",
                message= "User is already registered",
            )
        
        user = service.create_user(session, request);

        return SuccessResponse(
            data=user,
            message="User created successfully"
        )
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            error=str(e),
            message="Unknown error occurred"
        )


@user_router.delete(
    "/{user_id}",
    response_model=SuccessResponse[None],
    response_model_exclude_none=False,
    responses={
        404: {"model": ErrorResponse[str]},
        500: {"model": ErrorResponse[str]},
    }
)
async def delete_user(user_id: str, session: Session = Depends(get_session)):
    try:
        deleted = service.delete_user(session, user_id)
        
        if not deleted:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                error="USER_NOT_FOUND",
                message="User does not exist"
            )
        
        return SuccessResponse[None](
            data=None,
            message="User deleted successfully"
        ).model_dump(mode='json', exclude_none=False) 
    except APIException:
        raise
    except Exception as e:
        raise APIException(
            error=str(e),
            message="Failed to delete user"
        )

