import httpx
from fastapi import Depends, status
from loguru import logger
from sqlmodel import Session

from src.config import settings
from src.database.core import get_session
from src.entities.user import User
from src.exceptions import AuthenticationError


async def exchange_code_for_token(code: str) -> str:
    """Exchange GitHub OAuth code for access token"""
    headers = {
        "Accept": "application/json",
        "User-Agent": "apcc-api/1.0",
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

            if response.status_code != 200:
                logger.error(
                    f"Failed to get access token from GitHub domain: {response}"
                )
                raise AuthenticationError(
                    message="GitHub authorization failed",
                    debug="Failed to get access token from GitHub domain",
                )

            token_data = response.json()
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
    """Fetch GitHub user info"""
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
        "User-Agent": "apu-code-collab-api/1.0",
    }
    try:
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            response = await client.get(
                "https://api.github.com/user",
            )

            if response.status_code != 200:
                raise AuthenticationError()

            return response.json()
    except httpx.RequestError as e:
        raise AuthenticationError(
            status_code=502,
            error_code="GITHUB_USER_FETCH_NETWORK_ERROR",
            debug=str(e),
        )


async def persist_github_user_profile(session: Session, user: User):
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
