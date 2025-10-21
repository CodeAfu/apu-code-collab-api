# Requests
from pydantic import BaseModel, EmailStr, Field

from src.entities.user import User

class CreateUserRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    apu_id: str
    email: EmailStr
    password: str | None = None
    role: str = Field(default="student")
    is_active: bool = True


class GitHubUserRequest(BaseModel):
    # first_name: str = Field(min_length=1, max_length=50)
    # last_name: str = Field(min_length=1, max_length=50)
    # apu_id: str
    # email: EmailStr
    # role: str = "student",
    user_id: str
    github_id: int
    github_username: str
    github_avatar_url: str

class UpdateGitHubInfoRequest(BaseModel):
    github_id: int
    github_username: str

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    new_password_confirm: str
