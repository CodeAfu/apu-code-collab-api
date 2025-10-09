import os
from dotenv import load_dotenv
from fastapi import status, APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session

from src.models.api_response import ErrorResponse, SuccessResponse
from src.services.user_service import create_user, delete_user, get_user, get_users, is_unique_email
from src.models.api_exception import APIException
from src.models.user import CreateUserRequest, User
from src.utils.db import get_session

load_dotenv()
env = os.getenv("PYTHON_ENV")

user_router = APIRouter()

@user_router.get(
    "/",
    response_model=SuccessResponse[list[User]],
    response_model_exclude_none=True,
    responses={
        401: {"model": ErrorResponse[str]},
        500: {"model": ErrorResponse[str]}
    }
)
async def handle_get_users(session: Session = Depends(get_session)) -> JSONResponse:
    if env != "development":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": "Invalid Permission",
                "message": "You do not have permissions to access this endpoint",
            }
        )

    # TODO: Add proper role validation
    
    try:
        users = get_users(session)
        
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
async def handle_get_user(user_id: str, session: Session = Depends(get_session)) -> JSONResponse:
    try:
        user = get_user(session, user_id)
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
async def handle_create_user(request: CreateUserRequest, session: Session = Depends(get_session)) -> JSONResponse:
    try:
        email_is_unique = is_unique_email(session, request.email)
        if not email_is_unique:
            raise APIException(
                status_code=status.HTTP_409_CONFLICT,
                error= "Email is already already registered",
                message= "Email is already already registered",
            )
        
        user = create_user(session, request);

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
async def handle_delete_user(user_id: str, session: Session = Depends(get_session)):
    try:
        deleted = delete_user(session, user_id)
        
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

