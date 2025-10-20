from pydantic import BaseModel
from typing import Optional

class GitHubUser(BaseModel):
    github_id: int
    username: str
    email: Optional[str]
    avatar_url: str
    name: Optional[str]

class GitHubAuthCallback(BaseModel):
    code: str