from passlib.context import CryptContext

from src.auth.models import PasswordValidationResponse

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str | None) -> str:
    if password is None:
        return ""
    return bcrypt_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt_context.verify(plain_password, hashed_password)


def check_valid_password(password: str | None) -> PasswordValidationResponse:
    # Check if password is a string
    if not isinstance(password, str):
        return PasswordValidationResponse(valid=False, message="Password must be a string")
    
    # Check minimum length (e.g., 8 characters)
    if len(password) < 8:
        return PasswordValidationResponse(valid=False, message="Password must be at least 8 characters long")
    
    # Check for whitespaces
    if any(char.isspace() for char in password):
        return PasswordValidationResponse(valid=False, message="Password must not contain whitespaces")
    
    # Check for at least one uppercase letter
    if not any(char.isupper() for char in password):
        return PasswordValidationResponse(valid=False, message="Password must contain at least one uppercase letter")
    
    # Check for at least one lowercase letter
    if not any(char.islower() for char in password):
        return PasswordValidationResponse(valid=False, message="Password must contain at least one lowercase letter")
    
    # Check for at least one digit
    if not any(char.isdigit() for char in password):
        return PasswordValidationResponse(valid=False, message="Password must contain at least one digit")
    
    # Check for at least one special character
    special_characters = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
    if not any(char in special_characters for char in password):
        return PasswordValidationResponse(valid=False, message="Password must contain at least one special character")
    
    return PasswordValidationResponse(valid=True, message="Password is valid")
