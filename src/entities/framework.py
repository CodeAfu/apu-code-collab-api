from typing import TYPE_CHECKING

from cuid2 import Cuid
from sqlmodel import Field as SQLField
from sqlmodel import Relationship, SQLModel

from src.entities.github_repository import GithubRepositoryFrameworkLink

if TYPE_CHECKING:
    from src.entities.user import User
    from src.entities.github_repository import GithubRepository

cuid_gen = Cuid()


class UserFrameworkLink(SQLModel, table=True):
    __tablename__ = "user_framework_links"  # type: ignore

    user_id: str = SQLField(foreign_key="users.id", primary_key=True)
    framework_id: str = SQLField(foreign_key="frameworks.id", primary_key=True)


class Framework(SQLModel, table=True):
    __tablename__ = "frameworks"  # type: ignore

    id: str = SQLField(default_factory=cuid_gen.generate, primary_key=True)
    name: str = SQLField(unique=True, index=True)

    added_by: str | None = SQLField(default=None, foreign_key="users.id")

    users: list["User"] = Relationship(
        back_populates="preferred_frameworks",
        link_model=UserFrameworkLink,
    )

    repositories: list["GithubRepository"] = Relationship(
        back_populates="frameworks",
        link_model=GithubRepositoryFrameworkLink,
    )
