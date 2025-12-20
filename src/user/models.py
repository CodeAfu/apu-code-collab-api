# Requests
from datetime import datetime

from pydantic import BaseModel, EmailStr

from src.entities.user import UserRole


class RegisterUserRequest(BaseModel):
    apu_id: str
    password: str
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    role: UserRole | None = None


class CreateUserRequest(BaseModel):
    id: str
    first_name: str | None
    last_name: str | None
    apu_id: str
    email: EmailStr | None
    password: str
    role: UserRole = UserRole.STUDENT
    is_active: bool = True
    github_id: int | None
    github_username: str | None
    github_access_token: str | None
    github_avatar_url: str | None


class CreateUserResponse(BaseModel):
    id: str
    apu_id: str
    first_name: str | None
    last_name: str | None
    email: str | None
    role: UserRole
    github_username: str | None
    github_avatar_url: str | None
    is_active: bool
    created_at: datetime


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
