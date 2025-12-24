from passlib.context import CryptContext
from loguru import logger

from src.exceptions import InvalidPasswordException

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    try:
        return bcrypt_context.hash(password)
    except ValueError as e:
        logger.error(f"Error hashing password: {e}")
        raise ValueError("Invalid password") from e


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt_context.verify(plain_password, hashed_password)
    except ValueError as e:
        logger.error(f"Error verifying password: {e}")
        raise ValueError("Invalid password") from e


def check_valid_password(password: str | None) -> None:
    # Check if password is a string
    if not isinstance(password, str):
        raise InvalidPasswordException("Password must be a string")

    # Check minimum length (e.g., 8 characters)
    if len(password) < 8:
        raise InvalidPasswordException("Password must be at least 8 characters long")

    # Check for whitespaces
    if any(char.isspace() for char in password):
        raise InvalidPasswordException("Password must not contain whitespaces")

    # Check for at least one uppercase letter
    if not any(char.isupper() for char in password):
        raise InvalidPasswordException(
            "Password must contain at least one uppercase letter"
        )

    # Check for at least one lowercase letter
    if not any(char.islower() for char in password):
        raise InvalidPasswordException(
            "Password must contain at least one lowercase letter"
        )

    # Check for at least one digit
    if not any(char.isdigit() for char in password):
        raise InvalidPasswordException("Password must contain at least one digit")

    # Check for at least one special character
    # special_characters = "!@#$%^&*()_+-=[]{}|;:',.<>?/~`"
    # if not any(char in special_characters for char in password):
    #     raise InvalidPasswordException(
    #         "Password must contain at least one special character"
    #     )

    return None
