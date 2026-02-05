import json
from datetime import datetime
from typing import Sequence

import httpx
from fastapi import HTTPException, status
from loguru import logger
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.sql import case, literal
from sqlmodel import Session, col, select

from src.config import settings
from src.entities.framework import Framework
from src.entities.github_repository import GithubRepository
from src.entities.programming_language import ProgrammingLanguage
from src.entities.user import User
from src.exceptions import AuthenticationError
from src.github.models import GithubRepositoryStatsPayload


async def exchange_code_for_token(code: str) -> str:
    """
    Exchange a GitHub OAuth authorization code for the user's access token.

    Parameters:
        code (str): The authorization code received from GitHub's OAuth flow.

    Returns:
        access_token (str): The OAuth access token associated with the provided code.

    Raises:
        AuthenticationError: If GitHub returns a non-200 response, the response lacks an access token, or a network error occurs during the token exchange.
    """
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "apu-code-collab-api/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        async with httpx.AsyncClient(
            timeout=10.0, headers=headers, follow_redirects=True
        ) as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "code": code,
                },
            )

            validate_github_response(response)

            token_data = response.json()
            logger.debug(f"Token Data: {json.dumps(token_data, indent=2)}")
            access_token = token_data.get("access_token")

            if not access_token:
                logger.error("No access token present on the token data")
                raise AuthenticationError(
                    message="GitHub authorization failed",
                    debug="No access token present on the token data",
                )

            return access_token
    except httpx.RequestError as e:
        raise AuthenticationError(
            status_code=status.HTTP_502_BAD_GATEWAY,
            error_code="GITHUB_TOKEN_EXCHANGE_NETWORK_ERROR",
            debug=str(e),
        )


async def get_github_user_profile(access_token: str) -> dict:
    """
    Retrieve the authenticated GitHub user's profile using the provided OAuth access token.

    Parameters:
        access_token (str): GitHub OAuth access token sent in the Authorization header.

    Returns:
        dict: Parsed JSON object representing the GitHub user profile.

    Raises:
        AuthenticationError: If GitHub responds with a non-200 status or if a network/request error occurs (network errors are raised with status_code=502 and error_code="GITHUB_USER_FETCH_NETWORK_ERROR").
    """
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "apu-code-collab-api/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            response = await client.get(
                "https://api.github.com/user",
            )

            validate_github_response(response)

            return response.json()
    except httpx.RequestError as e:
        raise AuthenticationError(
            status_code=502,
            error_code="GITHUB_USER_FETCH_NETWORK_ERROR",
            debug=str(e),
        )


async def get_linked_repo(
    session: Session, github_username: str, repo_name: str
) -> GithubRepository | None:
    """
    Get GitHub repository entry from the database.

    Parameters:
        session (Session): Database session used to persist changes.
        github_username (str): The GitHub username of the repository owner.
        repo_name (str): The name of the repository to check.

    Returns:
        GithubRepository | None: The repository entry if found, otherwise None.
    """
    statement = (
        select(GithubRepository)
        .join(User)
        .where(
            User.github_username == github_username,
            GithubRepository.name == repo_name,
        )
    )
    logger.debug(f"Repository Query: {statement}")
    db_repo = session.exec(statement).first()
    logger.debug(f"Fetched Local Repo: {db_repo}")
    return db_repo


async def delete_linked_repo(
    session: Session,
    user_id: str,
    repo_id: str,
) -> GithubRepository:
    """
    Delete a repository entry that is shared with the website.

    Parameters:
        session (Session): Database session used to persist changes.
        user_id (str): The ID of the user who added the skills.
        repo_id (str): The ID of the repository to delete.

    Returns:
        GithubRepository: The repository entry that was deleted.
    """
    db_repo = session.exec(
        select(GithubRepository).where(GithubRepository.id == repo_id)
    ).first()
    logger.debug(f"Fetched Local Repo: {db_repo}")

    if not db_repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    if db_repo.user_id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this repository",
        )

    session.delete(db_repo)
    session.commit()

    return db_repo


async def update_repo_description(
    session: Session,
    id: str,
    description: str,
) -> GithubRepository:
    """
    Update the description of a repository entry that is shared with the website.

    Parameters:
        session (Session): Database session used to persist changes.
        id (str): The ID of the repository to check.
        description (str): The new description of the repository.

    Returns:
        GithubRepository: The repository entry if found.

    Raises:
        HTTPException(404): If the repository is not found.
    """
    db_repo = session.exec(
        select(GithubRepository).where(GithubRepository.id == id)
    ).first()
    logger.debug(f"Fetched Local Repo: {db_repo}")

    if not db_repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    db_repo.description = description

    session.add(db_repo)
    session.commit()
    session.refresh(db_repo)

    return db_repo


async def add_skills_to_repo(
    session: Session,
    user_id: str,
    id: str,
    skills: list[str],
) -> GithubRepository:
    """
    Add skills to a repository entry that is shared with the website.

    Parameters:
        session (Session): Database session used to persist changes.
        user_id (str): The ID of the user who added the skills.
        id (str): The ID of the repository to check.
        skills (list[str]): The list of skills to add to the repository.

    Returns:
        GithubRepository: The repository entry if found.

    Raises:
        HTTPException(404): If the repository is not found.
    """
    db_repo = session.exec(
        select(GithubRepository).where(GithubRepository.id == id)
    ).first()
    logger.debug(f"Fetched Local Repo: {db_repo}")

    if not db_repo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository not found",
        )

    db_repo.programming_languages.clear()
    db_repo.frameworks.clear()

    for name in set(skills):
        clean_name = name.strip()
        if not clean_name:
            continue

        stmt_lang = select(ProgrammingLanguage).where(
            col(ProgrammingLanguage.name).ilike(clean_name)  # ilike = case insensitive
        )
        existing_lang = session.exec(stmt_lang).first()

        if existing_lang:
            db_repo.programming_languages.append(existing_lang)
            continue

        stmt_fwork = select(Framework).where(
            col(Framework.name).ilike(clean_name)  # ilike = case insensitive
        )
        existing_fwork = session.exec(stmt_fwork).first()

        if existing_fwork:
            db_repo.frameworks.append(existing_fwork)
            continue

        new_fwork = Framework(name=clean_name, added_by=user_id)

        session.add(new_fwork)
        db_repo.frameworks.append(new_fwork)

    session.add(db_repo)
    session.commit()
    session.refresh(db_repo)

    return db_repo


async def link_repository(
    session: Session,
    user_id: str,
    repo_name: str,
    url: str,
    stats_payload: GithubRepositoryStatsPayload,
) -> GithubRepository:
    """
    Link a repository to the website by creating a new GithubRepository database entry.

    Parameters:
        session (Session): Database session used to persist changes.
        user_id (str): The ID of the user to associate with the repository.
        repo_name (str): The name of the repository to link.
        url (str): The URL of the repository.

    Returns:
        GithubRepository: The persisted repository entry.
    """
    repo = GithubRepository(
        user_id=user_id,
        name=repo_name,
        url=url,
        repository_language=stats_payload.repository_language,
        topics=stats_payload.topics,
        forks_count=stats_payload.forks_count,
        stargazers_count=stats_payload.stargazers_count,
        subscribers_count=stats_payload.subscribers_count,
        open_issues_count=stats_payload.open_issues_count,
    )

    session.add(repo)
    session.commit()
    session.refresh(repo)
    return repo


async def persist_github_user_profile(session: Session, user: User):
    """
    Persist GitHub profile fields into the provided User and save the updated user to the database.

    Fetches the GitHub profile using the user's `github_access_token`, updates `github_id`, `github_username`,
    and `github_avatar_url` on the given User, and commits the changes. If the user has no `github_access_token`,
    the function returns without altering the session.

    Parameters:
        session (Session): Database session used to persist changes.
        user (User): User entity to update; must have `github_access_token` set for profile retrieval.
    """
    if not user.github_access_token:
        return

    gh_profile = await get_github_user_profile(user.github_access_token)
    user.github_id = gh_profile["id"]
    user.github_username = gh_profile["login"]
    user.github_avatar_url = gh_profile.get("avatar_url")

    session.add(user)
    session.commit()
    session.refresh(user)

    logger.info(f"GitHub profile persisted successfully: {gh_profile}")


async def revoke_access_token(access_token: str) -> None:
    """
    Revoke a grant for an application.

    This deletes the specific token and removes the application from the user's
    authorized apps list on GitHub.

    Parameters:
        access_token (str): The access token to revoke.
    """
    url = f"https://api.github.com/applications/{settings.GITHUB_CLIENT_ID}/grant"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "apu-code-collab-api/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    body = {"access_token": access_token}

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # This endpoint requires Basic Auth using Client ID and Secret
            response = await client.request(
                method="DELETE",
                url=url,
                headers=headers,
                json=body,
                auth=(settings.GITHUB_CLIENT_ID, settings.GITHUB_CLIENT_SECRET),
            )

            validate_github_response(response)

            if response.status_code == 204:
                logger.info("GitHub token revoked successfully.")
            elif response.status_code == 404:
                logger.warning("GitHub token not found or already revoked.")
            else:
                logger.error(
                    f"Failed to revoke GitHub token. Status: {response.status_code}, Body: {response.text}"
                )
                raise HTTPException(
                    status_code=response.status_code,
                    detail=response.text,
                )

    except httpx.RequestError as e:
        logger.error(f"Network error while revoking GitHub token: {str(e)}")


def remove_repos_from_user(session: Session, user: User) -> None:
    """
    Remove all repositories from a user.

    Parameters:
        session (Session): Database session used to persist changes.
        user (User): The user to remove repositories from.
    """
    repos = session.exec(
        select(GithubRepository).where(GithubRepository.user_id == user.id)
    ).all()
    for repo in repos:
        session.delete(repo)


async def fetch_user_repos(access_token: str, page: int, size: int) -> dict:
    """
    Fetch a paginated list of repositories for the authenticated user.

    Parameters:
        access_token (str): The user's GitHub access token.
        page (int): The page number to fetch.
        size (int): The number of items per page.

    Returns:
        dict: A dictionary containing the paginated response data.
    """
    url = "https://api.github.com/user/repos"

    # Map API params to GitHub's expected params
    params = {"sort": "updated", "type": "all", "per_page": size, "page": page}

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "apu-code-collab-api/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers, params=params)

        validate_github_response(response)

        data = response.json()

        # Check the 'Link' header to see if a 'next' page exists
        # GitHub sends headers like: <url>; rel="next", <url>; rel="last"
        has_next = 'rel="next"' in response.headers.get("Link", "")

        return {"items": data, "page": page, "size": size, "has_next": has_next}


async def get_repo_information(
    access_token: str,
    github_username: str,
    repo_name: str,
) -> dict:
    """
    Fetch information about a repository.

    Parameters:
        repo_name (str): The name of the repository to fetch information for.

    Returns:
        dict: A dictionary containing the repository's name, description, and URL.
    """
    url = f"https://api.github.com/repos/{github_username}/{repo_name}"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "apu-code-collab-api/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if access_token:
        headers["Authorization"] = f"Bearer {access_token}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers)

        validate_github_response(response)

        data = response.json()
        logger.debug(f"Repository Data: {json.dumps(data, indent=2)}")

        return data


async def get_repo_collaborators(user: User, repo_name: str) -> list[dict]:
    """
    Fetch a list of collaborators for a given repository.

    Parameters:
        user (User): The user object representing the authenticated user.
        repo_name (str): The name of the repository to fetch collaborators for.

    Returns:
        list[dict]: A list of collaborator objects, each containing a `login` field.
    """
    url = (
        f"https://api.github.com/repos/{user.github_username}/{repo_name}/collaborators"
    )

    headers = {
        "Authorization": f"Bearer {user.github_access_token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "apu-code-collab-api/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, headers=headers)
        validate_github_response(response)
        data = response.json()
        return data


async def invite_collaborator(
    owner_token: str, owner_name: str, repo_name: str, collaborator_username: str
) -> dict:
    """
    Invite a collaborator to a repository.

    Parameters:
        owner_token (str): The GitHub access token of the repository owner.
        owner_name (str): The name of the repository owner.
        repo_name (str): The name of the repository to invite the collaborator to.
        collaborator_username (str): The username of the collaborator to invite.

    Returns:
        dict: A response object containing the HTTP status code and a message.
    """
    url = f"https://api.github.com/repos/{owner_name}/{repo_name}/collaborators/{collaborator_username}"

    headers = {
        "Authorization": f"Bearer {owner_token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "apu-code-collab-api/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    # permission can be 'pull', 'push', 'admin', 'maintain', or 'triage'
    data = {"permission": "push"}

    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.put(url, headers=headers, json=data)

        validate_github_response(response)

        logger.debug(f"Invite Response: {json.dumps(response.json(), indent=2)}")

        if response.status_code == 204:
            logger.info("User is already a collaborator.")
            return {"message": "User is already a collaborator."}

        return data


async def get_all_skills(session: Session) -> dict:
    """
    Fetch all skills from the database.

    Returns:
        dict: A list of skills.
    """
    framworks = session.exec(select(Framework)).all()
    programming_languages = session.exec(select(ProgrammingLanguage)).all()

    skills = []
    for framework in framworks:
        skills.append(framework.name)

    for programming_language in programming_languages:
        skills.append(programming_language.name)

    return {"items": skills}


async def get_all_programming_languages(
    session: Session,
) -> Sequence[ProgrammingLanguage]:
    """
    Fetch all programming languages from the database.

    Returns:
        Sequence[ProgrammingLanguage]: A list of programming languages.
    """
    return session.exec(select(ProgrammingLanguage)).all()


async def get_all_frameworks(session: Session) -> Sequence[Framework]:
    """
    Fetch all frameworks from the database.

    Returns:
        Sequence[Framework]: A list of frameworks.
    """
    return session.exec(select(Framework)).all()


async def get_dashboard_stats(session: Session, user_id: str) -> dict:
    """
    Retrieve the dashboard statistics for a user.
    This includes the total number of stars, forks, issues, and repositories,
    as well as the top 5 languages and top 5 repositories.

    Parameters:
        session (Session): The database session.
        user_id (str): The ID of the user to retrieve the statistics for.

    Returns:
        dict: A dictionary containing the dashboard statistics.
    """
    stmt = select(GithubRepository).where(GithubRepository.user_id == user_id)
    repos = session.exec(stmt).all()

    if not repos:
        return {
            "kpi": {
                "total_stars": 0,
                "total_forks": 0,
                "total_issues": 0,
                "total_repos": 0,
                "total_subscribers": 0,
            },
            "charts": {"languages": [], "top_repos": []},
        }

    total_stars = sum((r.stargazers_count or 0) for r in repos)
    total_forks = sum((r.forks_count or 0) for r in repos)
    total_issues = sum((r.open_issues_count or 0) for r in repos)
    total_subscribers = sum((r.subscribers_count or 0) for r in repos)
    total_repos = len(repos)

    language_map = {}
    for r in repos:
        lang = r.repository_language or "Unknown"
        language_map[lang] = language_map.get(lang, 0) + 1

    language_distribution = [{"name": k, "value": v} for k, v in language_map.items()]
    language_distribution.sort(key=lambda x: x["value"], reverse=True)

    sorted_by_stars = sorted(
        repos, key=lambda r: (r.stargazers_count or 0), reverse=True
    )
    top_5_repos = sorted_by_stars[:5]

    top_repos_data = [
        {
            "name": r.name,
            "stars": r.stargazers_count or 0,
            "forks": r.forks_count or 0,
            "issues": r.open_issues_count or 0,
        }
        for r in top_5_repos
    ]

    return {
        "kpi": {
            "total_stars": total_stars,
            "total_forks": total_forks,
            "total_issues": total_issues,
            "total_repos": total_repos,
            "total_subscribers": total_subscribers,
        },
        "charts": {"languages": language_distribution, "top_repos": top_repos_data},
    }


async def get_global_platform_stats(session: Session) -> dict:
    """
    Retrieve statistics across the ENTIRE database (All users, all repos).
    This includes the total number of stars, forks, issues, and repositories,
    as well as the top 5 languages and top 5 repositories.

    Parameters:
        session (Session): The database session.

    Returns:
        dict: A dictionary containing the global platform statistics.
    """
    stmt = select(
        func.sum(col(GithubRepository.stargazers_count)),
        func.sum(col(GithubRepository.forks_count)),
        func.count(col(GithubRepository.id)),
        func.sum(col(GithubRepository.open_issues_count)),
    )

    row = session.exec(stmt).first()

    if not row:
        total_stars = total_forks = total_repos = total_issues = 0
    else:
        total_stars, total_forks, total_repos, total_issues = row

    lang_stmt = (
        select(
            GithubRepository.repository_language, func.count(col(GithubRepository.id))
        )
        .where(col(GithubRepository.repository_language).is_not(None))
        .group_by(col(GithubRepository.repository_language))
        .order_by(func.count(col(GithubRepository.id)).desc())
        .limit(5)
    )
    top_languages = session.exec(lang_stmt).all()

    return {
        "kpi": {
            "platform_stars": total_stars or 0,
            "platform_forks": total_forks or 0,
            "platform_repos": total_repos or 0,
            "platform_issues": total_issues or 0,
        },
        "top_languages": [
            {"name": lang, "count": count} for lang, count in top_languages
        ],
    }


### GraphQL
async def get_all_local_repos_hydrated(
    session: Session,
    user: User,
    limit: int = 20,
    search: str | None = None,
    skills: list[str] | None = None,
    apu_id: str | None = None,
    github_username: str | None = None,
    cursor: str | None = None,  # TIMESTAMP|ID
) -> dict:
    """
    Fetch all shared repositories using GraphQL cursor pagination.

    Parameters:
        session (Session): Database session used to persist changes.
        user (User): The authenticated user.
        limit (int): The maximum number of repositories to fetch.
        search (str | None): The search query to filter repositories.
        skills (list[str] | None): The list of skills to filter repositories.
        apu_id (str | None): The APU ID of the owner to filter repositories.
        github_username (str | None): The GitHub username of the owner to filter repositories.
        cursor (str | None): The 'endCursor' from the previous response to fetch the next page.

    Returns:
        dict: A dictionary containing the hydrated repositories and the next cursor.
    """
    query = select(GithubRepository).join(User)

    user_lang_ids = [pl.id for pl in user.preferred_programming_languages]
    user_fw_ids = [fw.id for fw in user.preferred_frameworks]
    has_preferences = bool(user_lang_ids or user_fw_ids)

    # Define the "Relevance Score" expression (1 = Match, 0 = No Match)
    if has_preferences:
        match_lang = GithubRepository.programming_languages.any(  # type: ignore
            col(ProgrammingLanguage.id).in_(user_lang_ids)
        )
        match_fw = GithubRepository.frameworks.any(  # type: ignore
            col(Framework.id).in_(user_fw_ids)
        )
        # CASE WHEN (match_lang OR match_fw) THEN 1 ELSE 0 END
        relevance_score = case((or_(match_lang, match_fw), 1), else_=0)
    else:
        relevance_score = literal(0)

    if search:
        query = query.where(col(GithubRepository.name).ilike(f"%{search}%"))
    if apu_id:
        query = query.where(User.apu_id == apu_id)
    if github_username:
        query = query.where(User.github_username == github_username)
    if skills:
        query = query.where(
            or_(
                GithubRepository.programming_languages.any(  # type: ignore
                    col(ProgrammingLanguage.name).in_(skills)
                ),
                GithubRepository.frameworks.any(  # type: ignore
                    col(Framework.name).in_(skills)
                ),
            )
        )

    if cursor:
        try:
            # Split: "1|2023-01-01T12:00:00|abc..."
            parts = cursor.split("|")

            # Fallback for old cursors or if logic changes
            if len(parts) == 3:
                c_score = int(parts[0])
                c_time_str = parts[1]
                c_id = parts[2]
            else:
                # Handle legacy 2-part cursor (assume score 0 to reset)
                c_score = 0
                c_time_str = parts[0]
                c_id = parts[1]

            c_time = datetime.fromisoformat(c_time_str)

            # Complex Pagination Logic for (Score DESC, Time DESC, ID DESC)
            # 1. Score is LOWER (came after in sort)
            # 2. OR Score is SAME, but Time is OLDER
            # 3. OR Score is SAME, Time is SAME, but ID is SMALLER
            query = query.where(
                or_(
                    relevance_score < c_score,
                    and_(
                        relevance_score == c_score,
                        col(GithubRepository.created_at) < c_time,
                    ),
                    and_(
                        relevance_score == c_score,
                        col(GithubRepository.created_at) == c_time,
                        col(GithubRepository.id) < c_id,
                    ),
                )
            )
        except (ValueError, IndexError):
            logger.warning(f"Invalid cursor format: {cursor}")

    if has_preferences:
        query = query.order_by(relevance_score.desc())
    query = query.order_by(col(GithubRepository.created_at).desc())
    query = query.order_by(col(GithubRepository.id).desc())

    statement = (
        query.options(selectinload(GithubRepository.user))  # type: ignore
        .options(selectinload(GithubRepository.programming_languages))  # type: ignore
        .options(selectinload(GithubRepository.frameworks))  # type: ignore
        .limit(limit)
    )

    logger.debug(f"Repository Query: {statement}")

    db_repos = session.exec(statement).all()

    if not db_repos:
        return {"items": [], "next_cursor": None}

    next_cursor = None
    if len(db_repos) == limit:
        last_repo = db_repos[-1]
        # Recalculate score in Python for the cursor string
        # (Faster than selecting it explicitly in tuple)
        l_score = 0
        if has_preferences:
            repo_skill_ids = {s.id for s in last_repo.programming_languages}
            repo_fw_ids = {f.id for f in last_repo.frameworks}

            # Check intersection
            if (not repo_skill_ids.isdisjoint(user_lang_ids)) or (
                not repo_fw_ids.isdisjoint(user_fw_ids)
            ):
                l_score = 1

        next_cursor = f"{l_score}|{last_repo.created_at.isoformat()}|{last_repo.id}"

    query_fragments = []
    for index, repo in enumerate(db_repos):
        owner = repo.user.github_username
        name = repo.name

        fragment = f"""
        repo_{index}: repository(owner: "{owner}", name: "{name}") {{
            name
            description
            stargazer_count: stargazerCount
            fork_count: forkCount
            url
            owner {{
                login
                avatar_url: avatarUrl
            }}
            collaborators(first: 10) {{
                nodes {{
                    login
                    avatar_url: avatarUrl
                }}
            }}
        }}
        """
        query_fragments.append(fragment)

    full_query = f"query {{ {' '.join(query_fragments)} }}"

    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {user.github_access_token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "apu-code-collab-api/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json={"query": full_query})

        validate_github_response(response)

        result = response.json()
        hydrated_repos = []
        data = result.get("data", {}) or {}

        for index, db_repo in enumerate(db_repos):
            key = f"repo_{index}"
            gh_data = data.get(key)

            if gh_data:
                hydrated_repos.append(
                    {
                        "db_repo_id": db_repo.id,
                        "db_repo_description": db_repo.description,
                        "db_repo_skills": db_repo.skill_names,
                        "db_owner_id": db_repo.user.id,
                        "db_owner_first_name": db_repo.user.first_name,
                        "db_owner_last_name": db_repo.user.last_name,
                        "db_owner_apu_id": db_repo.user.apu_id,
                        **gh_data,
                    }
                )

        return {"items": hydrated_repos, "next_cursor": next_cursor}


async def fetch_user_repos_graphql(
    access_token: str, size: int, cursor: str | None = None
) -> dict:
    """
    Fetch repositories + collaborators using GraphQL cursor pagination.

    Args:
        cursor (str | None): The 'endCursor' from the previous response to fetch the next page.
    """
    url = "https://api.github.com/graphql"

    # GraphQL Query
    query = """
    query($size: Int!, $cursor: String) {
      viewer {
        repositories(first: $size, after: $cursor, orderBy: {field: UPDATED_AT, direction: DESC}) {
          pageInfo {
            hasNextPage
            endCursor
          }
          nodes {
            name
            htmlUrl
            description
            updatedAt
            collaborators(first: 5) {
              nodes {
                login
                avatarUrl
              }
            }
          }
        }
      }
    }
    """

    variables = {"size": size, "cursor": cursor}

    headers = {
        "Authorization": f"Bearer {access_token}",
        # GraphQL usually works best with standard JSON content type
        "Content-Type": "application/json",
        "User-Agent": "apu-code-collab-api/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    async with httpx.AsyncClient(timeout=10.0) as client:
        # GraphQL is always a POST request
        response = await client.post(
            url, headers=headers, json={"query": query, "variables": variables}
        )

        result = response.json()

        validate_github_response(response)

        # GraphQL puts errors in the JSON body even on 200 OK
        if "errors" in result:
            logger.error(f"GraphQL Query Error: {result['errors']}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="GitHub GraphQL query failed",
            )

        repo_data = result["data"]["viewer"]["repositories"]

        return {
            "items": repo_data["nodes"],
            "size": size,
            "has_next": repo_data["pageInfo"]["hasNextPage"],
            "next_cursor": repo_data["pageInfo"][
                "endCursor"
            ],  # Frontend must send this back for the next page
        }


def validate_github_response(response: httpx.Response) -> None:
    """
    Centralized validation for GitHub API responses.
    Checks for Auth errors, Rate Limits, and unexpected status codes.

    Parameters:
        response: The response object from httpx.
        success_codes: A list of status codes that should be considered "Success".
                       Defaults to [200].
    """
    if response.status_code == 401:
        logger.error("GitHub token expired or invalid")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="GitHub token invalid"
        )

    if response.status_code == 403:
        # Check specific header to distinguish Rate Limit vs Permission error
        if response.headers.get("x-ratelimit-remaining") == "0":
            logger.error("GitHub Rate Limit Exceeded (Quota)")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="System busy, please try again later.",
            )
        # Abuse detection mechanisms often send 403 with specific text
        if "secondary rate limit" in response.text.lower():
            logger.error("GitHub Secondary Rate Limit Triggered")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="System busy, please try again later.",
            )

    if response.status_code == 429:
        logger.error("GitHub Abuse Detection Triggered (429)")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="System busy, please try again later.",
        )

    if response.status_code not in range(200, 300):
        logger.error(f"GitHub API Error: {response.status_code} - {response.text}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GitHub API returned unexpected error: {response.status_code}",
        )
