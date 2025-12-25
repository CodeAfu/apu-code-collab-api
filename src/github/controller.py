from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlmodel import Session

from src.database.core import get_session
from src.github import service as github_service
from src.auth import service as auth_service
from src.rate_limiter import limiter

github_router = APIRouter(
    prefix="/api/v1/github",
)


@github_router.get("/repos")
@limiter.limit("15/minute")
async def get_shared_repos(
    request: Request,
    user: auth_service.CurrentActiveUser,
    session: Session = Depends(get_session),
    cursor: str = Query(description="Cursor for pagination"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> dict:
    """
    Retrieve a paginated list of repositories for the authenticated user.

    This endpoint requires the user to have a valid GitHub access token.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.
        cursor (str): The cursor for pagination.
        size (int): The number of items per page.

    Returns:
        dict: A paginated response containing the user's repositories.
    """
    if not user.github_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub access token required",
        )

    # Pass the pagination params to the service
    return await github_service.get_all_shared_repos_hydrated(
        session, user.github_access_token, size, cursor
    )


@github_router.get("/repos/{github_username}/{repo_name}")
@limiter.limit("15/minute")
async def get_repo_information(
    request: Request,
    user: auth_service.CurrentActiveUser,
    repo_name: str,
    github_username: str,
) -> dict:
    """
    Retrieve information about a repository.

    This endpoint requires the user to have a valid GitHub access token.

    Parameters:
        repo_name (str): The name of the repository to fetch information for.
        github_username (str): The GitHub username of the repository owner.

    Returns:
        dict: Repository information retrieved from GitHub repository API.
    """
    if not user.github_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub access token required",
        )

    if not repo_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing repository name",
        )

    if not github_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing GitHub username",
        )

    return await github_service.get_repo_information(
        user.github_access_token,
        github_username,
        repo_name,
    )
