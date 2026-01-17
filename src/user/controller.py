from typing import Sequence

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query, Path
from sqlmodel import Session
from loguru import logger

from src.auth import service as auth_service
from src.database.core import get_session
from src.entities.user import User
from src.github.models import GitHubLinkRequest, PaginatedRepoResponse
from src.github import service as github_service
from src.rate_limiter import limiter
from src.user import service as user_service
from src.user.models import (
    CreateUserRequest,
    UserReadResponse,
    UpdateUserProfileRequest,
    SkillRead,
    PersistPreferencesRequest,
    AdminUpdateUserRequest,
)

user_router = APIRouter(
    prefix="/api/v1/users",
)


@user_router.get(
    "/",
    response_model=list[User],
    response_model_exclude_none=True,
    response_model_exclude={"password_hash", "github_access_token"},
)
async def get_users(
    user: auth_service.CurrentActiveUser, session: Session = Depends(get_session)
) -> Sequence[User]:
    """
    Retrieve a list of all users.

    This endpoint does not require any authentication.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.
        session (Session): The database session dependency.

    Returns:
        list[User]: A list of all users.

    Raises:
        HTTPException(403): If the user is not an admin.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this endpoint",
        )

    users = user_service.get_users(session)
    return users


@user_router.get("/count")
@limiter.limit("60/minute")
async def get_user_count(
    request: Request,
    user: auth_service.CurrentActiveUser,
    session: Session = Depends(get_session),
) -> int:
    """
    Retrieve the total number of users in the system.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.
        session (Session): The database session dependency.

    Returns:
        int: The total number of users in the system.

    Raises:
        HTTPException(403): If the user is not an admin.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this endpoint",
        )
    return len(user_service.get_users(session))


@user_router.get(
    "/me",
    response_model=UserReadResponse,
    response_model_exclude_none=True,
    response_model_exclude={"password_hash", "github_access_token"},
)
@limiter.limit("60/minute")
async def get_user(
    request: Request,
    user: auth_service.CurrentActiveUser,
    session: Session = Depends(get_session),
) -> UserReadResponse:
    # await github_service.persist_github_user_profile(session, user)
    """
    Return the authenticated user's public profile as a UserRead model.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.

    Returns:
        UserRead: The user's data with `is_github_linked` set to `true` if a GitHub access token is present, `false` otherwise.
    """
    logger.info(f"User {user.id} requested their profile")
    logger.debug(f"User: {user}, Course: {user.university_course}")

    return UserReadResponse(
        **user.model_dump(),
        is_github_linked=bool(user.github_access_token),
        university_course=user.university_course if user.university_course else None,
        preferred_programming_languages=[
            SkillRead.model_validate(lang)
            for lang in user.preferred_programming_languages
        ]
        if user.preferred_programming_languages
        else [],
        preferred_frameworks=[
            SkillRead.model_validate(fw) for fw in user.preferred_frameworks
        ]
        if user.preferred_frameworks
        else [],
        github_repositories=user.github_repositories
        if user.github_repositories
        else None,
        # course_year=user.course_year.value if user.course_year else None,
    )


@user_router.put(
    "/me",
    status_code=status.HTTP_200_OK,
    response_model=UserReadResponse,
    response_model_exclude_none=True,
    response_model_exclude={"password_hash", "github_access_token"},
)
@limiter.limit("10/minute")
async def update_my_user_profile(
    request: Request,
    user: auth_service.CurrentActiveUser,
    update_request: UpdateUserProfileRequest,
    session: Session = Depends(get_session),
) -> UserReadResponse:
    """
    Update the authenticated user's profile.

    This endpoint does not override existing user data.
    If you wish to override user's existing data, use the admin endpoints.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.
        update_request (UpdateUserRequest): The payload containing the user's updated profile information.
        session (Session): The database session dependency.

    Returns:
        UserRead: The updated user object.
    """
    user = user_service.update_user_profile(session, user, update_request)
    return UserReadResponse(
        **user.model_dump(),
        is_github_linked=bool(user.github_access_token),
        university_course=user.university_course,
    )


@user_router.put(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    response_model=UserReadResponse,
    response_model_exclude_none=True,
    response_model_exclude={"password_hash", "github_access_token"},
)
@limiter.limit("10/minute")
async def update_user_by_id(
    request: Request,
    user: auth_service.CurrentActiveUser,
    update_request: AdminUpdateUserRequest,
    user_id: str = Path(description="The ID of the user to update."),
    session: Session = Depends(get_session),
) -> UserReadResponse:
    """
    Update a user's profile.

    This endpoint does not override existing user data.
    If you wish to override user's existing data, use the admin endpoints.

    Parameters:
        user_id (str): The ID of the user to update.
        update_request (AdminUpdateUserRequest): The updated user profile data.
        user (auth_service.CurrentActiveUser): The currently authenticated user.
        session (Session): The database session dependency.

    Returns:
        UserRead: The updated user object.

    Raises:
        HTTPException(403): If the user is not an admin.
        HTTPException(404): If no user is found with the provided ID.
        HTTPException(409): If the email is already in use.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this endpoint",
        )

    user = user_service.admin_update_user_profile(session, user_id, update_request)
    return UserReadResponse(
        **user.model_dump(),
        is_github_linked=bool(user.github_access_token),
        university_course=user.university_course,
    )


@user_router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=User,
    response_model_exclude_none=True,
    response_model_exclude={"password_hash", "github_access_token"},
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
    user_service.ensure_user_is_unique(
        session, create_request.email, create_request.apu_id
    )
    return user_service.create_user(session, create_request)


@user_router.delete(
    "/{user_id}",
    response_model=User,
    response_model_exclude_none=False,
)
@limiter.limit("10/minute")
async def delete_user(
    request: Request,
    user_id: str,
    user: auth_service.CurrentActiveUser,
    session: Session = Depends(get_session),
):
    """
    Delete a user from the system by their unique ID.

    Parameters:
        user_id (str): The unique identifier (CUID) of the user to delete.
        session (Session): The database session dependency.

    Returns:
        User: The user object that was deleted.

    Raises:
        HTTPException(403): If the user is not an admin.
        HTTPException(404): If no user is found with the provided ID.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this endpoint",
        )

    return await user_service.delete_user(session, user_id)


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

    This exchanges the provided GitHub OAuth code for an access token,
    retrieves the GitHub profile, stores GitHub-related fields
    (access token, GitHub ID, username, and avatar URL) on the authenticated user,
    and persists those changes to the database.

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
async def unlink_my_github_account(
    request: Request,
    user: auth_service.CurrentActiveUser,
    session: Session = Depends(get_session),
):
    """
    Unlink the authenticated user's GitHub account from their local user record.

    This removes the GitHub-related fields (access token, GitHub ID, username, and avatar URL)
    from the authenticated user, and persists those changes to the database.

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
    "/{user_id}/github/unlink",
    status_code=status.HTTP_200_OK,
    response_model=dict,
    response_model_exclude_none=True,
)
@limiter.limit("10/minute")
async def unlink_github_account_by_id(
    request: Request,
    user: auth_service.CurrentActiveUser,
    user_id: str = Path(
        description="The ID of the user whose GitHub account will be unlinked."
    ),
    session: Session = Depends(get_session),
):
    """
    Unlink the authenticated user's GitHub account from their local user record.

    This removes the GitHub-related fields (access token, GitHub ID, username, and avatar URL)
    from the selected user, and persists those changes to the database.

    Parameters:
        user_id (str): The ID of the user whose GitHub account will be unlinked.
        user (auth_service.CurrentActiveUser): The currently authenticated user whose account will be unlinked.
        session (Session): The database session dependency.

    Returns:
        dict: A message confirming successful unlinking, e.g. `{"message": "GitHub account unlinked successfully"}`.

    Raises:
        HTTPException(403): If the user is not an admin.
        HTTPException(404): If no user is found with the provided ID.
        HTTPException(401): If the user is not authenticated.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this endpoint",
        )

    db_user = user_service.get_user_by_id(session, user_id)
    if db_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if db_user.github_access_token:
        logger.info(f"Revoking GitHub token for user {db_user.id}...")
        await github_service.revoke_access_token(db_user.github_access_token)

    db_user.github_access_token = None
    db_user.github_id = None
    db_user.github_username = None
    db_user.github_avatar_url = None

    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    logger.info(f"User {db_user.id} unlinked GitHub account successfully")

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


@user_router.put(
    "/me/preferences/persist",
    response_model=UserReadResponse,
    response_model_exclude_none=True,
    response_model_exclude={"password_hash", "github_access_token"},
)
@limiter.limit("10/minute")
async def persist_preferences(
    request: Request,
    user: auth_service.CurrentActiveUser,
    persist_request: PersistPreferencesRequest,
    session: Session = Depends(get_session),
) -> UserReadResponse:
    """
    Persist the user's preferred programming languages and frameworks.

    This endpoint requires the user to have a valid GitHub access token.

    Parameters:
        user (auth_service.CurrentActiveUser): The currently authenticated user.
        persist_request (PersistPreferencesRequest): The payload containing the user's updated preferences.
        session (Session): The database session dependency.

    Returns:
        dict: A message confirming successful linking, e.g. `{"message": "Preferences persisted successfully"}`.

    Raises:
        HTTPException(401): If the user does not have a valid GitHub access token.
    """
    if not user.github_access_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="GitHub access token required",
        )

    logger.info(f"Persisting preferences for user {user.id}")
    logger.debug(f"Persist Request: {persist_request}")

    user = await user_service.persist_preferences(
        session,
        user,
        persist_request.programming_languages,
        persist_request.frameworks,
    )

    return UserReadResponse(
        **user.model_dump(),
        is_github_linked=bool(user.github_access_token),
        university_course=user.university_course if user.university_course else None,
        github_repositories=user.github_repositories
        if user.github_repositories
        else None,
        preferred_programming_languages=[
            SkillRead.model_validate(lang)
            for lang in user.preferred_programming_languages
        ]
        if user.preferred_programming_languages
        else [],
        preferred_frameworks=[
            SkillRead.model_validate(fw) for fw in user.preferred_frameworks
        ]
        if user.preferred_frameworks
        else [],
    )
