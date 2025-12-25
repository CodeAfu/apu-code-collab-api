from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlmodel import Session
from loguru import logger

from src.auth import service as auth_service
from src.config import settings
from src.database.core import get_session
from src.entities.user import User
from src.github.models import GitHubLinkRequest, PaginatedRepoResponse
from src.github import service as github_service
from src.rate_limiter import limiter
from src.user import service
from src.user.models import CreateUserRequest, UserRead

user_router = APIRouter(
    prefix="/api/v1/users",
)


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


@user_router.get(
    "/me/github/unlink",
    status_code=status.HTTP_200_OK,
    response_model=dict,
    response_model_exclude_none=True,
)
@limiter.limit("10/minute")
async def unlink_github_account(
    request: Request,
    user: auth_service.CurrentActiveUser,
    session: Session = Depends(get_session),
):
    """
    Unlink the authenticated user's GitHub account from their local user record.

    This removes the GitHub-related fields (access token, GitHub ID, username, and avatar URL) from the authenticated user, and persists those changes to the database.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user whose account will be unlinked.
        session (Session): The database session dependency.

    Returns:
        dict: A message confirming successful unlinking, e.g. `{"message": "GitHub account unlinked successfully"}`.
    """
    if user.github_access_token:
        logger.info(f"Revoking GitHub token for user {user.id}...")
        await github_service.revoke_access_token(user.github_access_token)

    user.github_access_token = None
    user.github_id = None
    user.github_username = None
    user.github_avatar_url = None

    session.add(user)
    session.commit()
    session.refresh(user)

    logger.info(f"User {user.id} unlinked GitHub account successfully")

    return {"message": "GitHub account unlinked successfully"}


@user_router.get(
    "/me/github/repos",
    response_model=PaginatedRepoResponse,
)
@limiter.limit("10/minute")
async def get_github_repos(
    request: Request,
    user: auth_service.CurrentActiveUser,
    session: Session = Depends(get_session),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
):
    """
    Retrieve a paginated list of repositories for the authenticated user.

    This endpoint requires the user to have a valid GitHub access token.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.
        page (int): The page number to fetch (1-based).
        size (int): The number of items per page.

    Returns:
        PaginatedRepoResponse: A paginated response containing the user's repositories.
    """
    if not user.github_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub access token required",
        )

    # Pass the pagination params to the service
    return await github_service.fetch_user_repos(
        user.github_access_token, page=page, size=size
    )


@user_router.get(
    "/me/github/{repo_name}/collaborators",
)
@limiter.limit("10/minute")
async def get_repo_collaborators(
    request: Request,
    user: auth_service.CurrentActiveUser,
    repo_name: str,
    session: Session = Depends(get_session),
):
    """
    Retrieve a list of collaborators for a given repository.

    This endpoint requires the user to have a valid GitHub access token.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.
        repo_name (str): The name of the repository to fetch collaborators for.
        session (Session): The database session dependency.

    Returns:
        list[dict]: A list of collaborator objects, each containing a `login` field.
    """
    if not user.github_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub access token required",
        )

    return await github_service.get_repo_collaborators(user, repo_name)
