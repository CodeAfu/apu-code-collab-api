from dotenv import load_dotenv
from fastapi import Request, status, APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlmodel import Session

from src.rate_limiter import limiter
from src.user import service
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
    
    users = service.get_users(session)
    return [user.model_dump(exclude={"password_hash"}) for user in users]


@user_router.get(
    "/{user_id}",
    response_model=User,
    response_model_exclude_none=True,
    response_model_exclude={"password_hash"}
)
@limiter.limit("1/second")
async def get_user(
    request: Request,
    user_id: str,
    session: Session = Depends(get_session)
) -> JSONResponse:
    return service.get_user(session, user_id)


@user_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=User,
    response_model_exclude_none=True,
    response_model_exclude={"password_hash"},
)
@limiter.limit("10/minute")
async def create_user(
    request: Request,
    create_request: CreateUserRequest,
    session: Session = Depends(get_session)
) -> JSONResponse:
    service.ensure_user_is_unique(session, create_request.email, create_request.apu_id)
    return service.create_user(session, create_request)


@user_router.delete(
    "/{user_id}",
    response_model=User,
    response_model_exclude_none=False,
)
@limiter.limit("10/minute")
async def delete_user(request: Request, user_id: str, session: Session = Depends(get_session)):
    return service.delete_user(session, user_id)
