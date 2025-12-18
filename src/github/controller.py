import secrets
from datetime import timedelta
from urllib.parse import urlencode

from dotenv import load_dotenv
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session
from src.github import service as github_service

from src.auth import service as auth_service
from src.config import settings
from src.database.core import get_session
from src.user import service as user_service

load_dotenv()

github_router = APIRouter(
    prefix="/api/v1/auth/github",
)
scopes = ["user:email", "read:org", "read:user"]


@github_router.get("/login")
async def github_login():
    """Redirect to GitHub App Auth"""
    state = secrets.token_urlsafe(32)
    params = {
        "client_id": settings.GITHUB_APP_CLIENT_ID,
        "redirect_uri": settings.GITHUB_CALLBACK_URL,
        "scope": " ".join(scopes),
        "state": state,
    }
    resp = RedirectResponse(
        f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    )
    # Persist state; simplest: short‑lived, HttpOnly cookie
    resp.set_cookie(
        "gh_oauth_state", state, max_age=600, httponly=True, secure=True, samesite="lax"
    )
    return resp


@github_router.get("/callback")
async def github_callback(
    code: str,
    state: str,
    request: Request,
    session: Session = Depends(get_session),
):
    """
    Handle GitHub OAuth callback
    - If user exists (by email), link their GitHub account
    - User must still have APU ID from initial registration
    """

    # Validate state
    if request.cookies.get("gh_oauth_state") != state:
        return RedirectResponse(
            f"{settings.FRONTEND_URL}/login?error=github_state_mismatch"
        )

    # Exchange code for GitHub access token
    gh_access_token = await github_service.exchange_code_for_token(code)

    # Get GitHub user info
    gh_user = await github_service.get_github_user(gh_access_token)

    # GitHub users MUST have a public email
    if not gh_user.get("email"):
        return RedirectResponse(f"{settings.FRONTEND_URL}/login?error=github_no_email")

    # Check if user exists by email
    user = user_service.get_user_by_email(session, gh_user["email"])

    if not user:
        # User doesn't exist - they need to register with APU credentials first
        return RedirectResponse(
            f"{settings.FRONTEND_URL}/register?error=no_account&email={gh_user['email']}"
        )

    # User exists - link/update their GitHub info
    user.github_id = gh_user["id"]
    user.github_username = gh_user["login"]
    user.github_avatar_url = gh_user.get("avatar_url")

    session.add(user)
    session.commit()
    session.refresh(user)

    # Create JWT tokens
    access_token = auth_service.create_access_token(
        user.email,
        user.id,
        user.apu_id,
        user.role,
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    refresh_token = auth_service.create_refresh_token(
        user.email,
        user.id,
        user.apu_id,
        user.role,
        timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    # Redirect to frontend with tokens
    resp = RedirectResponse(
        f"{settings.FRONTEND_URL}/github/auth/callback?access_token={access_token}&ttl={settings.ACCESS_TOKEN_EXPIRE_MINUTES}"
    )

    resp.set_cookie(
        "access_token",
        access_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * settings.ACCESS_TOKEN_EXPIRE_MINUTES,
    )
    resp.set_cookie(
        "refresh_token",
        refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=24 * 60 * settings.REFRESH_TOKEN_EXPIRE_DAYS,
    )

    return resp


@github_router.post("/disconnect")
async def github_disconnect(
    current_user: auth_service.CurrentUser, session: Session = Depends(get_session)
):
    """Disconnect GitHub account from logged-in user"""
    if not current_user.user_id:
        raise HTTPException(status_code=404, detail="User not found")

    user = user_service.get_user(session, current_user.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.github_id:
        raise HTTPException(status_code=400, detail="No GitHub account linked")

    # Unlink GitHub account
    user.github_id = None
    user.github_username = None
    user.github_avatar_url = None

    session.add(user)
    session.commit()

    return {"message": "GitHub account disconnected successfully"}


@github_router.get("/status")
async def github_status(
    current_user: auth_service.CurrentUser, session: Session = Depends(get_session)
):
    """Check if current user has GitHub account linked"""
    if not current_user.user_id:
        raise HTTPException(status_code=404, detail="User not found")

    user = user_service.get_user(session, current_user.user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "connected": user.github_id is not None,
        "github_username": user.github_username,
        "github_avatar_url": user.github_avatar_url,
    }
