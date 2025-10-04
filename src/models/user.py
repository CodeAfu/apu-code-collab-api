from datetime import datetime
from pydantic import BaseModel, EmailStr, Field
from cuid2 import Cuid
from sqlmodel import SQLModel, Field as SQLField

cuid_gen = Cuid()

class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: str = SQLField(default_factory=cuid_gen.generate, primary_key=True)
    name: str = SQLField(min_length=1, max_length=100, index=True)
    email: str = SQLField(unique=True, index=True)
    student_id: str | None = SQLField(default=None)
    is_active: bool = SQLField(default=True)
    role: str = SQLField(default="user")
    created_at: datetime = SQLField(default_factory=datetime.now)

# Requests
class CreateUserRequest(SQLModel):
    name: str = SQLField(min_length=1, max_length=100)
    email: EmailStr  # EmailStr for validation
    student_id: str | None = None
    role: str = "user"
    is_active: bool = True