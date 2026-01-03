from datetime import datetime
from typing import TYPE_CHECKING

from cuid2 import Cuid
from sqlmodel import Column, DateTime, Relationship, SQLModel, UniqueConstraint, JSON
from sqlmodel import Field as SQLField

if TYPE_CHECKING:
    from src.entities.user import User

cuid_gen = Cuid()


class GithubRepository(SQLModel, table=True):
    __tablename__ = "github_repositories"  # type: ignore

    __table_args__ = (UniqueConstraint("user_id", "name", name="uix_user_id_name"),)

    # Required fields for initialization
    id: str = SQLField(default_factory=cuid_gen.generate, primary_key=True)
    user_id: str = SQLField(foreign_key="users.id", index=True)
    name: str = SQLField(min_length=1, max_length=50, index=True)
    url: str = SQLField(unique=True, min_length=1, max_length=200)

    # Info to share on website (Local)
    description: str | None = SQLField(default=None, max_length=1000)
    collaborators: list[str] = SQLField(
        default=[], sa_column=Column(JSON)
    )  # List of github usernames
    contributors: list[str] = SQLField(
        default=[], sa_column=Column(JSON)
    )  # List of github usernames
    skills: list[str] = SQLField(default=[], sa_column=Column(JSON))  # List of strings

    # Timestamps
    created_at: datetime = SQLField(
        default_factory=datetime.now, sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = SQLField(
        default_factory=datetime.now, sa_column=Column(DateTime(timezone=True))
    )

    # Relationships (Navigation properties)
    user: "User" = Relationship(back_populates="github_repositories")
