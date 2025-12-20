from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenData(BaseModel):
    user_id: str | None = None
    apu_id: str | None = None
    token_type: str = "access"


class PasswordValidationResponse(BaseModel):
    valid: bool
    message: str
