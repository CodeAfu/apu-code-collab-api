from typing import Sequence

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlmodel import Session
from loguru import logger

from src.auth import service as auth_service
from src.config import settings
from src.database.core import get_session
from src.entities.user import User
from src.github.models import GitHubLinkRequest
from src.github import service as github_service
from src.rate_limiter import limiter
from src.user import service
from src.user.models import CreateUserRequest, UserRead

load_dotenv()

user_router = APIRouter(
    prefix="/api/v1/users",
)
unknown_error_message = "Unknown error occurred"


@user_router.get(
    "/",
    response_model=list[User],
    response_model_exclude_none=True,
    response_model_exclude={"password_hash"},
)
async def get_users(session: Session = Depends(get_session)) -> Sequence[User]:
    """
    Retrieve a list of all users in the system.

    This endpoint is restricted to development environments only. Attempting to access
    it in production will result in a 403 Forbidden error.

    Parameters:
        session (Session): The database session dependency.

    Returns:
        Sequence[User]: A list of all user objects stored in the database.

    Raises:
        HTTPException(403): If the application is running in a non-development environment.
    """
    # TODO: Protect this better
    if not settings.is_development:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "Invalid Permission",
                "message": "You are not allowed to accesss this endpoint",
            },
        )

    users = service.get_users(session)
    return users


@user_router.get(
    "/me",
    response_model=UserRead,
    response_model_exclude_none=True,
    response_model_exclude={"password_hash", "github_access_token"},
)
@limiter.limit("60/minute")
async def get_user(
    request: Request,
    user: auth_service.CurrentActiveUser,
    session: Session = Depends(get_session),
) -> UserRead:
    # await github_service.persist_github_user_profile(session, user)
    """
    Return the authenticated user's public profile as a UserRead model.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.

    Returns:
        UserRead: The user's data with `is_github_linked` set to `true` if a GitHub access token is present, `false` otherwise.
    """
    return UserRead(
        **user.model_dump(), is_github_linked=bool(user.github_access_token)
    )


@user_router.post(
    "/me/github/link",
)
# @limiter.limit("10/hour")
async def link_github_account(
    request: Request,
    user: auth_service.CurrentActiveUser,
    payload: GitHubLinkRequest,
    session: Session = Depends(get_session),
) -> dict:
    """
    Link the authenticated user's GitHub account to their local user record.

    This exchanges the provided GitHub OAuth code for an access token, retrieves the GitHub profile, stores GitHub-related fields (access token, GitHub ID, username, and avatar URL) on the authenticated user, and persists those changes to the database.

    Parameters:
        payload (GitHubLinkRequest): Payload containing the GitHub OAuth `code` to exchange for an access token.
        user (auth_service.CurrentActiveUser): The currently authenticated user whose account will be linked.

    Returns:
        dict: A message confirming successful linking, e.g. `{"message": "GitHub account linked successfully"}`.
    """
    gh_token = await github_service.exchange_code_for_token(payload.code)
    gh_profile = await github_service.get_github_user_profile(gh_token)

    logger.info(f"GitHub Profile Retrieved: {gh_profile}")
    user.github_access_token = gh_token
    user.github_id = gh_profile["id"]
    user.github_username = gh_profile["login"]
    user.github_avatar_url = gh_profile.get("avatar_url")

    session.add(user)
    session.commit()
    session.refresh(user)

    logger.info(f"User {user.id} linked GitHub account successfully")

    return {"message": "GitHub account linked successfully"}


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
    session: Session = Depends(get_session),
) -> User:
    """
    Register a new user in the system.

    This endpoint validates the uniqueness of the provided email and APU ID before
    creating the user record.

    Parameters:
        create_request (CreateUserRequest): The payload containing user registration details (email, APU ID, password, etc.).
        session (Session): The database session dependency.

    Returns:
        User: The newly created user object.

    Raises:
        HTTPException(400): If the email or APU ID is already in use.
    """
    service.ensure_user_is_unique(session, create_request.email, create_request.apu_id)
    return service.create_user(session, create_request)


@user_router.delete(
    "/{user_id}",
    response_model=User,
    response_model_exclude_none=False,
)
@limiter.limit("10/minute")
async def delete_user(
    request: Request, user_id: str, session: Session = Depends(get_session)
):
    """
    Delete a user from the system by their unique ID.

    Parameters:
        user_id (str): The unique identifier (CUID) of the user to delete.
        session (Session): The database session dependency.

    Returns:
        User: The user object that was deleted.

    Raises:
        HTTPException(404): If no user is found with the provided ID.
    """
    return service.delete_user(session, user_id)
