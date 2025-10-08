import os
from dotenv import load_dotenv
from fastapi import status, APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from src.models.api_exception import APIException
from src.models.user import CreateUserRequest
from src.services.user_service import UserService, get_user_service

load_dotenv()
env = os.getenv("PYTHON_ENV")

user_router = APIRouter()

@user_router.get("/")
async def get_users(user_service: UserService = Depends(get_user_service)) -> JSONResponse:
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
        users = user_service.get_users()
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "data": [user.model_dump(mode="json", exclude_none=True) for user in users],
                "message": "Users retrieved successfully"
            },
        )
    except Exception as e:
        return APIException(
            error=str(e),
            message="Unknown error occurred"
        )


@user_router.get("/{user_id}", response_model_exclude_none=True)
# @limiter.limit("1/second")
async def get_user(user_id: str, user_service: UserService = Depends(get_user_service)) -> JSONResponse:
    try:
        user = user_service.get_user(user_id)
        if not user:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                error="User does not exist",
                message="User does not exist"
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": user.model_dump(mode="json", exclude_none=True),
                "message": "User retrieved successfully",
            }
        )
    except APIException:
        raise
    except Exception as e:
        return APIException(
            error=str(e),
            message="Unknown error occurred"
        )
            

@user_router.post("", response_model_exclude_none=True)
async def create_user(request: CreateUserRequest,user_service: UserService = Depends(get_user_service)) -> JSONResponse:
    try:
        email_is_unique = user_service.is_unique_email(request.email)

        if not email_is_unique:
            raise APIException(
                status_code=status.HTTP_409_CONFLICT,
                error= "Email is already already registered",
                message= "Email is already already registered",
            )
        
        user = user_service.create_user(request);

        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "data": user.model_dump(mode="json", exclude_none=True),
                "message": "User created successfully"
            }
        )
    except APIException:
        raise
    except Exception as e:
        return APIException(
            error=str(e),
            message="Unknown error occurred"
        )

@user_router.delete("/{user_id}", response_model_exclude_none=True)
async def delete_user(user_id: str, user_service: UserService = Depends(get_user_service)):
    try:
        deleted = user_service.delete_user(user_id)
        
        if not deleted:
            raise APIException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "USER_NOT_FOUND",
                    "message": "User does not exist"
                }
            )
        
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "success": True,
                "data": None,
                "message": "User deleted successfully"
            }
        )
    except APIException:
        raise
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "message": "Failed to delete user"
            }
        )

