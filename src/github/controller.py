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
from typing import Sequence
from sqlmodel import Session

from src.auth import service as auth_service
from src.database.core import get_session
from src.entities.framework import Framework
from src.entities.github_repository import GithubRepository
from src.entities.programming_language import ProgrammingLanguage
from src.github import service as github_service
from src.github.models import (
    AddSkillsRequest,
    UpdateRepoDescriptionRequest,
    GithubRepositoryStatsPayload,
)
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
    search: str | None = Query(None, description="Search query"),
    skills: list[str] | None = Query(
        None, description="Frameworks and Programming Languages"
    ),
    apu_id: str | None = Query(None, description="Owner's APU ID"),
    github_username: str | None = Query(None, description="Owner's GitHub username"),
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
        session,
        user.github_access_token,
        size,
        search,
        skills,
        apu_id,
        github_username,
        cursor,
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
) -> dict | None:
    """
    Retrieve a respository entry that is shared with the website.

    This endpoint requires the user to have a valid GitHub access token.

    Parameters:
        repo_name (str): The name of the repository to check.
        github_username (str): The GitHub username of the repository owner.

    Returns:
        dict | None: The repository entry if found, otherwise None.
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

    db_repo = await github_service.get_linked_repo(
        session,
        github_username,
        repo_name,
    )

    if not db_repo:
        return None

    return {
        **db_repo.model_dump(),
        "skills": db_repo.skill_names,
    }


@github_router.delete("/repos/local/{id}")
@limiter.limit("15/minute")
async def delete_local_repo(
    request: Request,
    user: auth_service.CurrentActiveUser,
    id: str = Path(description="The ID of the repository."),
    session: Session = Depends(get_session),
) -> GithubRepository:
    """
    Delete a repository entry that is shared with the website.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.
        id (str): The ID of the repository to delete.
        session (Session): The database session dependency.

    Returns:
        GithubRepository: The repository entry that was deleted.

    Raises:
        HTTPException(401): If the user is not authenticated.
        HTTPException(403): If the user does not have permission to delete the repository.
        HTTPException(404): If the repository is not found.
    """
    if not user.github_access_token:
        logger.error("GitHub access token required")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub access token required",
        )

    return await github_service.delete_linked_repo(
        session,
        user.id,
        id,
    )


@github_router.post("/repos/{id}/description")
@limiter.limit("15/minute")
async def update_repo_local_description(
    request: Request,
    user: auth_service.CurrentActiveUser,
    id: str = Path(description="The ID of the repository."),
    payload: UpdateRepoDescriptionRequest = Body(
        ..., description="The new description of the repository."
    ),
    session: Session = Depends(get_session),
) -> GithubRepository:
    """
    Update the description of a repository entry that is shared with the website.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.
        id (str): The ID of the repository to check.
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

    if not id:
        logger.error("Missing repository ID")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing repository ID",
        )

    return await github_service.update_repo_description(
        session,
        id,
        payload.description,
    )


@github_router.post("/repos/{id}/skills")
@limiter.limit("15/minute")
async def add_skills_to_repo_local(
    request: Request,
    user: auth_service.CurrentActiveUser,
    id: str = Path(description="The ID of the repository."),
    payload: AddSkillsRequest = Body(
        ..., description="The list of skills to add to the repository."
    ),
    session: Session = Depends(get_session),
) -> GithubRepository:
    """
    Add skills to a repository entry that is shared with the website.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.
        id (str): The ID of the repository to check.
        skills (AddSkillsRequest): The list of skills to add to the repository.

    Returns:
        GithubRepository: The repository entry if found

    Raises:
        HTTPException(400): If the repository id is missing on the request.
        HTTPException(401): If the user is not authenticated.
        HTTPException(404): If the repository is not found.
    """
    if not user.github_access_token:
        logger.error("GitHub access token required")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub access token required",
        )

    if not id:
        logger.error("Missing repository ID")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing repository ID",
        )

    return await github_service.add_skills_to_repo(
        session,
        user.id,
        id,
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
    stats_payload: GithubRepositoryStatsPayload = Body(
        ..., description="The statistics of the repository."
    ),
    session: Session = Depends(get_session),
) -> GithubRepository:
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
        stats_payload,
    )


@github_router.get("/repos/skills", response_model_exclude={"added_by"})
@limiter.limit("15/minute")
async def get_all_skills(
    request: Request,
    user: auth_service.CurrentActiveUser,
    session: Session = Depends(get_session),
) -> dict:
    """
    Retrieve the full list of skills for a github repository.

    This endpoint requires the user to have a valid GitHub access token.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.

    Returns:
        dict: A paginated response containing the user's skills.
    """
    return await github_service.get_all_skills(session)


@github_router.get("/repos/programming_languages")
@limiter.limit("15/minute")
async def get_all_programming_languages(
    request: Request,
    user: auth_service.CurrentActiveUser,
    session: Session = Depends(get_session),
) -> Sequence[ProgrammingLanguage]:
    """
    Retrieve the full list of programming languages for a github repository.

    This endpoint requires the user to have a valid GitHub access token.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.

    Returns:
        Sequence[ProgrammingLanguage]: A list of programming languages.
    """
    return await github_service.get_all_programming_languages(session)


@github_router.get("/repos/frameworks")
@limiter.limit("15/minute")
async def get_all_frameworks(
    request: Request,
    user: auth_service.CurrentActiveUser,
    session: Session = Depends(get_session),
) -> Sequence[Framework]:
    """
    Retrieve the full list of frameworks for a github repository.

    This endpoint requires the user to have a valid GitHub access token.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.

    Returns:
        Sequence[Framework]: A list of frameworks.
    """
    return await github_service.get_all_frameworks(session)


@github_router.get("/dashboard-stats")
@limiter.limit("15/minute")
async def get_dashboard_stats(
    request: Request,
    user: auth_service.CurrentActiveUser,
    session: Session = Depends(get_session),
) -> dict:
    """
    Retrieve the dashboard statistics for the authenticated user.

    This endpoint requires the user to have a valid GitHub access token.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.

    Returns:
        dict: A dictionary containing the dashboard statistics.
    """
    return await github_service.get_dashboard_stats(session, user.id)


@github_router.get("/global-dashboard-stats")
@limiter.limit("15/minute")
async def get_global_platform_stats(
    request: Request,
    session: Session = Depends(get_session),
) -> dict:
    """
    Retrieve the global platform statistics.

    This endpoint does not require any authentication.

    Parameters:
        session (Session): The database session.

    Returns:
        dict: A dictionary containing the global platform statistics.
    """
    return await github_service.get_global_platform_stats(session)
