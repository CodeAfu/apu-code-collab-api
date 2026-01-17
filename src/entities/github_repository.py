from datetime import datetime
from typing import TYPE_CHECKING

from cuid2 import Cuid
from sqlmodel import Column, DateTime, Relationship, SQLModel, UniqueConstraint, JSON
from sqlmodel import Field as SQLField, Integer

if TYPE_CHECKING:
    from src.entities.user import User
    from src.entities.framework import Framework
    from src.entities.programming_language import ProgrammingLanguage

cuid_gen = Cuid()


class GithubRepositoryFrameworkLink(SQLModel, table=True):
    __tablename__ = "github_repository_framework_links"  # type: ignore

    repository_id: str = SQLField(
        foreign_key="github_repositories.id", primary_key=True, ondelete="CASCADE"
    )
    framework_id: str = SQLField(foreign_key="frameworks.id", primary_key=True)


class GithubRepositoryProgrammingLanguageLink(SQLModel, table=True):
    __tablename__ = "github_repository_programming_language_links"  # type: ignore

    repository_id: str = SQLField(
        foreign_key="github_repositories.id", primary_key=True, ondelete="CASCADE"
    )
    programming_language_id: str = SQLField(
        foreign_key="programming_languages.id", primary_key=True
    )


class GithubRepository(SQLModel, table=True):
    __tablename__ = "github_repositories"  # type: ignore
    __table_args__ = (UniqueConstraint("user_id", "name", name="uix_user_id_name"),)

    # Required fields for initialization
    id: str = SQLField(default_factory=cuid_gen.generate, primary_key=True)
    user_id: str = SQLField(foreign_key="users.id", index=True, ondelete="CASCADE")
    name: str = SQLField(min_length=1, max_length=50, index=True)
    url: str = SQLField(unique=True, min_length=1, max_length=200)

    # Statistics
    repository_language: str | None = SQLField(
        default=None, max_length=50
    )  # Language of the repository detected by GitHub
    topics: list[str] = SQLField(default=[], sa_column=Column(JSON))
    forks_count: int = SQLField(default=0, sa_column=Column(Integer))
    stargazers_count: int = SQLField(default=0, sa_column=Column(Integer))
    subscribers_count: int = SQLField(default=0, sa_column=Column(Integer))
    open_issues_count: int = SQLField(default=0, sa_column=Column(Integer))

    # Info to share on website (Local)
    description: str | None = SQLField(default=None, max_length=1000)
    collaborators: list[str] = SQLField(
        default=[], sa_column=Column(JSON)
    )  # List of github usernames
    contributors: list[str] = SQLField(
        default=[], sa_column=Column(JSON)
    )  # List of github usernames
    frameworks: list["Framework"] = Relationship(
        back_populates="repositories", link_model=GithubRepositoryFrameworkLink
    )  # Recommended frameworks for collaborators (user assigned)
    programming_languages: list["ProgrammingLanguage"] = Relationship(
        back_populates="repositories",
        link_model=GithubRepositoryProgrammingLanguageLink,
    )  # Recommended langauge for collaborators (user assigned)

    # Timestamps
    created_at: datetime = SQLField(
        default_factory=datetime.now, sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = SQLField(
        default_factory=datetime.now, sa_column=Column(DateTime(timezone=True))
    )

    # Relationships (Navigation properties)
    user: "User" = Relationship(back_populates="github_repositories")

    @property
    def skill_names(self) -> list[str]:
        langs = [lang.name for lang in self.programming_languages]
        fworks = [fwork.name for fwork in self.frameworks]
        return langs + fworks

    @property
    def skills(self):
        langs = [lang for lang in self.programming_languages]
        fworks = [fwork for fwork in self.frameworks]
        return langs + fworks
