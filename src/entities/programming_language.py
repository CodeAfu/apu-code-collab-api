from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field as SQLField, Relationship
from cuid2 import Cuid

from src.entities.github_repository import GithubRepositoryProgrammingLanguageLink

if TYPE_CHECKING:
    from src.entities.user import User
    from src.entities.github_repository import GithubRepository

cuid_gen = Cuid()


class UserProgrammingLanguageLink(SQLModel, table=True):
    __tablename__ = "user_programming_language_links"  # type: ignore

    user_id: str = SQLField(
        foreign_key="users.id", primary_key=True, ondelete="CASCADE"
    )
    programming_language_id: str = SQLField(
        foreign_key="programming_languages.id", primary_key=True, ondelete="CASCADE"
    )


class ProgrammingLanguage(SQLModel, table=True):
    __tablename__ = "programming_languages"  # type: ignore

    id: str = SQLField(default_factory=cuid_gen.generate, primary_key=True)
    name: str = SQLField(unique=True, index=True)

    added_by: str | None = SQLField(default=None, foreign_key="users.id")

    users: list["User"] = Relationship(
        back_populates="preferred_programming_languages",
        link_model=UserProgrammingLanguageLink,
    )

    repositories: list["GithubRepository"] = Relationship(
        back_populates="programming_languages",
        link_model=GithubRepositoryProgrammingLanguageLink,
    )
