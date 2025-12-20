from datetime import datetime
from typing import TYPE_CHECKING

from cuid2 import Cuid
from sqlmodel import Field as SQLField, Relationship
from sqlmodel import SQLModel

if TYPE_CHECKING:
    from src.entities.user import User

cuid_gen = Cuid()


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"  # type: ignore

    id: str = SQLField(default_factory=cuid_gen.generate, primary_key=True)
    user_id: str = SQLField(foreign_key="users.id", index=True)
    token: str = SQLField(index=True)

    user: "User" = Relationship(back_populates="refresh_tokens")

    expires_at: datetime = SQLField(default=None)
    created_at: datetime = SQLField(default_factory=datetime.now)
    updated_at: datetime = SQLField(default_factory=datetime.now)
