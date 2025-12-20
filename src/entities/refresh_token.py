from datetime import datetime

from cuid2 import Cuid
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel

cuid_gen = Cuid()


class RefreshToken(SQLModel, table=True):
    __tablename__ = "refresh_tokens"  # type: ignore

    id: str = SQLField(default_factory=cuid_gen.generate, primary_key=True)
    user_id: str = SQLField(index=True)
    token: str = SQLField(index=True)

    expires_at: datetime = SQLField(default=None)
    created_at: datetime = SQLField(default_factory=datetime.now)
    updated_at: datetime = SQLField(default_factory=datetime.now)
