from datetime import timedelta
import os
from fastapi.responses import RedirectResponse
import httpx;
from http.client import HTTPException
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Request
from github import Github
from requests import Session

from src.api_response import ErrorResponse, SuccessResponse
from src.database.core import get_session
from src.entities.user import User
from src.github import service as github_service
from src.user import service as user_service
from src.auth import service as auth_service

load_dotenv()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
GITHUB_CALLBACK_URL = os.getenv("GITHUB_CALLBACK_URL")
FRONTEND_URL = os.getenv("FRONTEND_URL")

github_router = APIRouter(prefix="/api/v1/auth/github",)


@github_router.get("/login")
async def github_login():
    """Redirect to GitHub OAuth"""
    return RedirectResponse(
        f"https://github.com/login/oauth/authorize?"
        f"client_id={GITHUB_CLIENT_ID}&"
        f"scope=user:email"
    )


@github_router.get("/callback")
async def github_callback(code: str, session: Session = Depends(get_session)):
    """
    Handle GitHub OAuth callback
    - If user exists (by email), link their GitHub account
    - User must still have APU ID from initial registration
    """
    
    # Exchange code for GitHub access token
    gh_access_token = await github_service.exchange_code_for_token(code)
    
    # Get GitHub user info
    gh_user = await github_service.get_github_user(gh_access_token)
    
    # GitHub users MUST have a public email
    if not gh_user.get("email"):
        return RedirectResponse(
            f"{FRONTEND_URL}/login?error=github_no_email"
        )
    
    # Check if user exists by email
    user = user_service.get_user_by_email(session, gh_user["email"])
    
    if not user:
        # User doesn't exist - they need to register with APU credentials first
        return RedirectResponse(
            f"{FRONTEND_URL}/register?error=no_account&email={gh_user['email']}"
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
        timedelta(minutes=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    refresh_token = auth_service.create_refresh_token(
        user.email,
        user.id,
        user.apu_id,
        timedelta(days=auth_service.REFRESH_TOKEN_EXPIRE_DAYS)
    )
    
    # Redirect to frontend with tokens
    return RedirectResponse(
        f"{FRONTEND_URL}/auth/callback?"
        f"access_token={access_token}&"
        f"refresh_token={refresh_token}"
    )


@github_router.post("/disconnect")
async def github_disconnect(
    current_user: auth_service.CurrentUser,
    session: Session = Depends(get_session)
):
    """Disconnect GitHub account from logged-in user"""
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
    current_user: auth_service.CurrentUser,
    session: Session = Depends(get_session)
):
    """Check if current user has GitHub account linked"""
    user = user_service.get_user(session, current_user.user_id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "connected": user.github_id is not None,
        "github_username": user.github_username,
        "github_avatar_url": user.github_avatar_url
    }