from datetime import datetime, timezone
from typing import TYPE_CHECKING

from cuid2 import Cuid
from sqlmodel import Field as SQLField, Relationship, Column, DateTime
from sqlmodel import SQLModel

if TYPE_CHECKING:
    from src.entities.user import User

cuid_gen = Cuid()


def utc_now():
    return datetime.now(timezone.utc)


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"  # type: ignore

    id: str = SQLField(default_factory=cuid_gen.generate, primary_key=True)
    user_id: str = SQLField(foreign_key="users.id", index=True, ondelete="CASCADE")
    token: str = SQLField(index=True)
    revoked: bool = SQLField(default=False)

    user: "User" = Relationship(back_populates="refresh_tokens")

    expires_at: datetime = SQLField(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    revoked_at: datetime | None = SQLField(
        default=None, sa_column=Column(DateTime(timezone=True))
    )
    created_at: datetime = SQLField(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True))
    )
    updated_at: datetime = SQLField(
        default_factory=utc_now, sa_column=Column(DateTime(timezone=True))
    )
