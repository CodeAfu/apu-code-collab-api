from pydantic import BaseModel

class Token(BaseModel):
    access_token: str
    github_access_token: str | None
    refresh_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: str | None = None
    apu_id: str | None = None
    email: str | None = None
    token_type: str = "access"

class PasswordValidationResponse(BaseModel):
    valid: bool
    message: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str