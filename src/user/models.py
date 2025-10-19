# Requests
from pydantic import BaseModel, EmailStr, Field

class CreateUserRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    apu_id: str | None = None
    email: EmailStr
    password: str
    role: str = "student"
    is_active: bool = True

class RegisterUserRequest(BaseModel):
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)
    apu_id: str
    email: EmailStr
    password: str
    role: str = "student"
    is_active: bool = True

class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
    new_password_confirm: str
