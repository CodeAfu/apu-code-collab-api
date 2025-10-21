from pydantic import BaseModel
from typing import Optional

class GitHubToken(BaseModel):
    access_token: str
    token_type: str
    scope: str
    expires_in: int | None

class GitHubUser(BaseModel):
    github_id: int
    username: str
    email: Optional[str]
    avatar_url: str
    name: Optional[str]

class GitHubAuthCallback(BaseModel):
    code: str