from datetime import datetime
from enum import Enum
from cuid2 import Cuid
from pydantic import model_validator
from sqlmodel import SQLModel, Field as SQLField

cuid_gen = Cuid()


class UserRole(str, Enum):
    STUDENT = "student"
    TEACHER = "teacher"
    ADMIN = "admin"


class User(SQLModel, table=True):
    __tablename__ = "users"  # type: ignore

    id: str = SQLField(default_factory=cuid_gen.generate, primary_key=True)
    apu_id: str = SQLField(
        min_length=8,
        max_length=8,
        regex=r"^T[CP]\d{6}$",
        unique=True,
        index=True,
        default=None,
    )
    first_name: str = SQLField(min_length=1, max_length=50, index=True)
    last_name: str = SQLField(min_length=1, max_length=50, index=True)
    email: str = SQLField(unique=True, index=True)
    password_hash: str = SQLField(min_length=60, max_length=255)
    is_active: bool = SQLField(default=True)
    role: UserRole = SQLField(default=UserRole.STUDENT)

    github_id: int | None = SQLField(unique=True, index=True)
    github_username: str | None = SQLField(min_length=1, max_length=50, unique=True)
    github_access_token: str | None = SQLField(min_length=1, max_length=200)
    github_avatar_url: str | None = SQLField(min_length=1, max_length=200)

    created_at: datetime = SQLField(default_factory=datetime.now)
    updated_at: datetime = SQLField(default_factory=datetime.now)

    @model_validator(mode="before")
    @classmethod
    def set_role_from_id(cls, values):
        apu_id = values.get("apu_id")

        if apu_id:
            if apu_id.startswith("TP"):
                values["role"] = UserRole.STUDENT
            elif apu_id.startswith("TC"):
                values["role"] = UserRole.TEACHER

        return values
