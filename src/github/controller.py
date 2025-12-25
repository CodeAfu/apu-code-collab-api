from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from sqlmodel import Session

from src.database.core import get_session
from src.github import service as github_service
from src.auth import service as auth_service
from src.rate_limiter import limiter

github_router = APIRouter(
    prefix="/api/v1/github",
)


@github_router.get(
    "/shared-repos",
)
@limiter.limit("15/minute")
async def get_shared_repos(
    request: Request,
    user: auth_service.CurrentActiveUser,
    session: Session = Depends(get_session),
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
) -> list[dict]:
    """
    Retrieve a paginated list of repositories for the authenticated user.

    This endpoint requires the user to have a valid GitHub access token.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.
        page (int): The page number to fetch (1-based).
        size (int): The number of items per page.

    Returns:
        list[dict]: A paginated response containing the user's repositories.
    """
    if not user.github_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub access token required",
        )

    # Pass the pagination params to the service
    return await github_service.get_all_shared_repos_hydrated(
        session, user.github_access_token, size, page
    )
