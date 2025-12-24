from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field as SQLField, Relationship
from cuid2 import Cuid

if TYPE_CHECKING:
    from src.entities.user import User

cuid_gen = Cuid()


class UniversityCourse(SQLModel, table=True):
    __tablename__ = "university_courses"  # type: ignore

    id: str = SQLField(default_factory=cuid_gen.generate, primary_key=True)
    name: str = SQLField(unique=True, index=True)
    code: str | None = SQLField(default=None, unique=True, index=True)

    users: list["User"] = Relationship(back_populates="university_course")
