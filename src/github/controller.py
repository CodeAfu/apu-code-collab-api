import os
import httpx;
from http.client import HTTPException
from dotenv import load_dotenv
from fastapi import APIRouter, Depends
from github import Github
from requests import Session

from src.database.core import get_session
from src.entities.user import User

load_dotenv()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL")

github_router = APIRouter(prefix="/api/v1/github",)


@github_router.get("/auth")
async def github_login():
    """Redirect to GitHub OAuth"""
    redirect_uri = f"{FRONTEND_URL}/api/auth/callback"
    scope = "repo read:user read:org"
    
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
    )
    
    return {"url": github_auth_url}


@github_router.get("/callback")
async def github_callback(code: str, db: Session = Depends(get_session)):
    """Handle GitHub OAuth callback"""
    
    # Exchange code for access token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
        )
    
    token_data = token_response.json()
    access_token = token_data.get("access_token")
    
    if not access_token:
        raise HTTPException(status_code=400, detail="Failed to get access token")
    
    # Get user info from GitHub
    g = Github(access_token)
    github_user = g.get_user()
    
    # Check if user exists
    user = db.query(User).filter(User.github_id == github_user.id).first()
    
    if user:
        # Update existing user
        user.github_access_token = access_token
        user.github_username = github_user.login
    else:
        # Create new user
        user = User(
            github_id=github_user.id,
            github_username=github_user.login,
            github_access_token=access_token,
        )
        db.add(user)
    
    db.commit()
    db.refresh(user)
    
    # Return user info and token (you'll want to use JWT in production)
    return {
        "user_id": user.id,
        "github_username": user.github_username,
        "github_id": user.github_id,
    }


@github_router.get("/repos/{user_id}")
async def get_repos(user_id: int, db: Session = Depends(get_session)):
    """Get user's GitHub repositories"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    g = Github(user.github_access_token)
    repos = g.get_user().get_repos()
    
    return [{
        "id": repo.id,
        "name": repo.name,
        "full_name": repo.full_name,
        "description": repo.description,
        "html_url": repo.html_url,
        "private": repo.private,
    } for repo in repos]


@github_router.post("/create-project/{user_id}")
async def create_project(
    user_id: int,
    project_data: dict,
    db: Session = Depends(get_session)
):
    """Create a new GitHub repository and add collaborators"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    g = Github(user.github_access_token)
    github_user = g.get_user()
    
    try:
        # Create repository
        repo = github_user.create_repo(
            name=project_data["name"],
            description=project_data.get("description", ""),
            private=project_data.get("private", False),
            auto_init=True,  # Initialize with README
        )
        
        # Add collaborators
        for username in project_data.get("collaborators", []):
            repo.add_to_collaborators(username, permission="push")
        
        return {
            "success": True,
            "repo_url": repo.html_url,
            "repo_name": repo.full_name,
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@github_router.get("/user/{user_id}")
async def get_github_user(user_id: int, db: Session = Depends(get_session)):
    """Get GitHub user info"""
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    g = Github(user.github_access_token)
    github_user = g.get_user()
    
    return {
        "username": github_user.login,
        "name": github_user.name,
        "avatar_url": github_user.avatar_url,
        "bio": github_user.bio,
        "public_repos": github_user.public_repos,
    }
