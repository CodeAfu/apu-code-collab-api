import os
import httpx
from dotenv import load_dotenv
from src.exceptions import AuthenticationError

load_dotenv()

GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")


async def exchange_code_for_token(code: str) -> str:
    """Exchange GitHub OAuth code for access token"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://github.com/login/oauth/access_token",
            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"}
        )
        
        if response.status_code != 200:
            raise AuthenticationError(
                error="Failed to get access token from GitHub domain", 
                message="GitHub authorization failed"
            )
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise AuthenticationError(
                error="No access token present on the token data",
                message="GitHub authorization failed"
            )
        
        return access_token


async def get_github_user(access_token: str) -> dict:
    """Fetch GitHub user info"""
    async with httpx.AsyncClient() as client:
        response = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json"
            }
        )
        
        if response.status_code != 200:
            raise AuthenticationError()
        
        return response.json()