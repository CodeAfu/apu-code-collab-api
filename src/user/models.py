# Requests
from datetime import datetime

from pydantic import BaseModel, EmailStr, ConfigDict

from src.entities.github_repository import GithubRepository
from src.entities.university_course import UniversityCourse
from src.entities.user import CourseYear, UserRole


class SkillRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str


class UserReadResponse(BaseModel):
    id: str
    apu_id: str
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    is_active: bool
    role: UserRole

    # Github Public Info
    github_id: int | None = None
    github_username: str | None = None
    github_avatar_url: str | None = None
    is_github_linked: bool

    course_year: str | None = None

    # FK
    university_course: UniversityCourse | None = None
    github_repositories: list[GithubRepository] | None = None
    preferred_programming_languages: list[SkillRead] | None = None
    preferred_frameworks: list[SkillRead] | None = None

    created_at: datetime
    updated_at: datetime


class PersistPreferencesRequest(BaseModel):
    programming_languages: list[str] | None = None
    frameworks: list[str] | None = None


class UpdateUserProfileRequest(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    email: EmailStr | None = None
    university_course: UniversityCourse | None = None
    course_year: CourseYear | None = None


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
