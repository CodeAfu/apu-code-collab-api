from typing import Sequence

from sqlmodel import Session, select
from loguru import logger
from sqlalchemy.exc import IntegrityError

from src.entities.user import User
from src.exceptions import UserAlreadyExistsException, UserDoesNotExistException
from src.user.models import CreateUserRequest
from src.utils import security
from src.exceptions import ConflictException, InternalException


def get_users(session: Session) -> Sequence[User]:
    """
    Retrieve all users from the database.

    Parameters:
        session (Session): The database session.

    Returns:
        Sequence[User]: A list of all User entities.
    """
    return session.exec(select(User)).all()


def get_user(session: Session, user_id: str) -> User:
    """
    Retrieve a specific user by their unique ID.

    Parameters:
        session (Session): The database session.
        user_id (str): The unique identifier (CUID) of the user.

    Returns:
        User: The found user entity.

    Raises:
        UserDoesNotExistException: If no user exists with the given ID.
    """
    user = session.exec(select(User).where(User.id == user_id)).first()

    if not user:
        raise UserDoesNotExistException()

    return user


def get_user_by_email(session: Session, email: str) -> User | None:
    """
    Retrieve a user by their email address.

    Parameters:
        session (Session): The database session.
        email (str): The email address to search for.

    Returns:
        User | None: The user entity if found, otherwise None.
    """
    return session.exec(select(User).where(User.email == email)).first()


def get_user_by_apu_id(session: Session, apu_id: str) -> User | None:
    """
    Retrieve a user by their APU ID (e.g., TP number).

    Parameters:
        session (Session): The database session.
        apu_id (str): The APU ID to search for.

    Returns:
        User | None: The user entity if found, otherwise None.
    """
    return session.exec(select(User).where(User.apu_id == apu_id)).first()


def is_unique_email(session: Session, email: str) -> bool:
    """
    Check if an email address is available (not already in use).

    Parameters:
        session (Session): The database session.
        email (str): The email address to check.

    Returns:
        bool: True if the email is unique (does not exist in DB), False otherwise.
    """
    return session.exec(select(User).where((User.email == email))).first() is None


def is_unique_apu_id(session: Session, apu_id: str) -> bool:
    """
    Check if an APU ID is available (not already in use).

    Parameters:
        session (Session): The database session.
        apu_id (str): The APU ID to check.

    Returns:
        bool: True if the APU ID is unique, False otherwise.
    """
    return session.exec(select(User).where((User.apu_id == apu_id))).first() is None


def ensure_user_is_unique(session: Session, email: str | None, apu_id: str) -> None:
    """
    Verify that a user with the provided credentials does not already exist.

    This checks for a collision based on APU ID and, if provided, Email.

    Parameters:
        session (Session): The database session.
        email (str | None): The email address to check (optional).
        apu_id (str): The APU ID to check.

    Raises:
        UserAlreadyExistsException: If a user matching the criteria already exists.
    """
    conditions = [User.apu_id == apu_id]

    if email is not None:
        conditions.append(User.email == email)

    statement = select(User).where(*conditions)

    user = session.exec(statement).first()

    if user:
        raise UserAlreadyExistsException()


def create_user(session: Session, request: CreateUserRequest) -> User:
    """
    Create a new user record in the database.

    This function handles password hashing, populates the User entity from the request,
    and commits the transaction. It also handles database integrity errors (like duplicate keys).

    Parameters:
        session (Session): The database session.
        request (CreateUserRequest): The data transfer object containing user details.

    Returns:
        User: The newly created and persisted User entity.

    Raises:
        ConflictException: If a unique constraint violation occurs (e.g., email already exists).
        InternalException: If an unexpected error occurs during creation.
    """
    try:
        password_hash = security.get_password_hash(request.password)

        logger.info(f"Creating user: {request.apu_id}")

        user = User(
            first_name=request.first_name,
            last_name=request.last_name,
            apu_id=request.apu_id,
            email=request.email,
            password_hash=password_hash,
            role=request.role,
            github_id=request.github_id,
            github_username=request.github_username,
            github_access_token=request.github_access_token,
            github_avatar_url=request.github_avatar_url,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user
    except IntegrityError as e:
        session.rollback()
        if "unique constraint" in str(e).lower():
            logger.error(f"Email already registered: {request.email}")
            raise ConflictException("Email already registered")
        logger.exception(f"Failed to register user: {request.apu_id}")
        raise
    except Exception:
        session.rollback()
        logger.exception(f"Failed to register user: {request.apu_id}")
        raise InternalException("Failed to create user")


def delete_user(session: Session, user_id: str) -> User:
    """
    Permanently remove a user from the database.

    Parameters:
        session (Session): The database session.
        user_id (str): The unique ID of the user to delete.

    Returns:
        User: The user entity that was deleted.

    Raises:
        UserDoesNotExistException: If the user ID was not found.
    """
    user = session.exec(select(User).where(User.id == user_id)).first()

    if not user:
        raise UserDoesNotExistException()

    session.delete(user)
    session.commit()

    return user
