from fastapi import (
    APIRouter,
    Body,
    Depends,
    HTTPException,
    Path,
    Query,
    Request,
    status,
)
from loguru import logger
from sqlmodel import Session

from src.auth import service as auth_service
from src.database.core import get_session
from src.entities.github_repository import GithubRepository
from src.github import service as github_service
from src.github.models import AddSkillsRequest, UpdateRepoDescriptionRequest
from src.rate_limiter import limiter

github_router = APIRouter(
    prefix="/api/v1/github",
)


@github_router.get("/repos")
@limiter.limit("15/minute")
async def get_local_repos(
    request: Request,
    user: auth_service.CurrentActiveUser,
    session: Session = Depends(get_session),
    cursor: str | None = Query(
        None, description="Cursor for pagination (TIMESTAMP|ID)"
    ),
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
        logger.error("GitHub access token required")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub access token required",
        )

    # Pass the pagination params to the service
    return await github_service.get_all_local_repos_hydrated(
        session, user.github_access_token, size, cursor
    )


@github_router.get("/repos/{github_username}/{repo_name}")
@limiter.limit("15/minute")
async def get_repo_information(
    request: Request,
    user: auth_service.CurrentActiveUser,
    repo_name: str = Path(description="The name of the repository."),
    github_username: str = Path(
        description="The GitHub username of the repository owner."
    ),
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
        logger.error("GitHub access token required")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub access token required",
        )

    if not repo_name:
        logger.error("Missing repository name")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing repository name",
        )

    if not github_username:
        logger.error("Missing GitHub username")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing GitHub username",
        )

    return await github_service.get_repo_information(
        user.github_access_token,
        github_username,
        repo_name,
    )


@github_router.get("/repos/local/{github_username}/{repo_name}")
@limiter.limit("15/minute")
async def get_repo_local(
    request: Request,
    user: auth_service.CurrentActiveUser,
    repo_name: str = Path(description="The name of the repository."),
    github_username: str = Path(
        description="The GitHub username of the repository owner."
    ),
    session: Session = Depends(get_session),
) -> GithubRepository | None:
    """
    Retrieve a respository entry that is shared with the website.

    This endpoint requires the user to have a valid GitHub access token.

    Parameters:
        repo_name (str): The name of the repository to check.
        github_username (str): The GitHub username of the repository owner.

    Returns:
        GithubRepository | None: The repository entry if found, otherwise None.
    """
    if not user.github_access_token:
        logger.error("GitHub access token required")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub access token required",
        )

    if not repo_name:
        logger.error("Missing repository name")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing repository name",
        )

    if not github_username:
        logger.error("Missing GitHub username")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing GitHub username",
        )

    return await github_service.get_linked_repo(
        session,
        github_username,
        repo_name,
    )


@github_router.post("/repos/{github_username}/{repo_name}/description")
@limiter.limit("15/minute")
async def update_repo_local_description(
    request: Request,
    user: auth_service.CurrentActiveUser,
    repo_name: str = Path(description="The name of the repository."),
    github_username: str = Path(
        description="The GitHub username of the repository owner."
    ),
    payload: UpdateRepoDescriptionRequest = Body(
        ..., description="The new description of the repository."
    ),
    session: Session = Depends(get_session),
):
    """
    Update the description of a repository entry that is shared with the website.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.
        repo_name (str): The name of the repository to check.
        github_username (str): The GitHub username of the repository owner.
        payload (UpdateRepoDescriptionRequest): The new description of the repository.

    Returns:
        GithubRepository: The repository entry if found

    Raises:
        HTTPException(404): If the repository is not found.
    """
    if not user.github_access_token:
        logger.error("GitHub access token required")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub access token required",
        )

    if not repo_name:
        logger.error("Missing repository name")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing repository name",
        )

    if not github_username:
        logger.error("Missing GitHub username")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing GitHub username",
        )

    return await github_service.update_repo_description(
        session,
        github_username,
        repo_name,
        payload.description,
    )


@github_router.post("/repos/{github_username}/{repo_name}/skills")
@limiter.limit("15/minute")
async def add_skills_to_repo_local(
    request: Request,
    user: auth_service.CurrentActiveUser,
    repo_name: str = Path(description="The name of the repository."),
    github_username: str = Path(
        description="The GitHub username of the repository owner."
    ),
    payload: AddSkillsRequest = Body(
        ..., description="The list of skills to add to the repository."
    ),
    session: Session = Depends(get_session),
):
    """
    Add skills to a repository entry that is shared with the website.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.
        repo_name (str): The name of the repository to check.
        github_username (str): The GitHub username of the repository owner.
        skills (AddSkillsRequest): The list of skills to add to the repository.

    Returns:
        GithubRepository: The repository entry if found

    Raises:
        HTTPException(404): If the repository is not found.
    """
    if not user.github_access_token:
        logger.error("GitHub access token required")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub access token required",
        )

    if not repo_name:
        logger.error("Missing repository name")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing repository name",
        )

    if not github_username:
        logger.error("Missing GitHub username")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing GitHub username",
        )

    return await github_service.add_skills_to_repo(
        session,
        github_username,
        repo_name,
        payload.skills,
    )


@github_router.post("/repos")
@limiter.limit("15/minute")
async def link_repo_local(
    request: Request,
    user: auth_service.CurrentActiveUser,
    user_id: str = Query(
        str, description="The ID of the user to associate with the repository."
    ),
    repo_name: str = Query(str, description="The name of the repository."),
    url: str = Query(str, description="The URL of the repository."),
    session: Session = Depends(get_session),
):
    """
    Persist a repository entry in the database.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.
        user_id (str): The ID of the user to associate with the repository.
        repo_name (str): The name of the repository.
        url (str): The URL of the repository.

    Returns:
        GithubRepository: The persisted repository entry.
    """
    if not user.github_access_token:
        logger.error("GitHub access token required")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub access token required",
        )

    if not url:
        logger.error("Missing repository URL")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing repository URL",
        )

    if not repo_name:
        logger.error("Missing repository name")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing repository name",
        )

    return await github_service.link_repository(
        session,
        user_id,
        repo_name,
        url,
    )
