from typing import Sequence

from fastapi import APIRouter, Depends, Request, Path, HTTPException, status
from sqlmodel import Session, SQLModel

from src.database.core import get_session
from src.entities.programming_language import ProgrammingLanguage
from src.programming_languages import service as plang_service
from src.rate_limiter import limiter
from src.entities.user import User
from src.auth.service import get_current_user

plang_router = APIRouter(
    prefix="/api/v1/programming_languages",
)


class ProgrammingLanguageRequest(SQLModel):
    name: str


@plang_router.get("/")
@limiter.limit("60/minute")
async def get_programming_languages(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Sequence[ProgrammingLanguage]:
    """
    Retrieve a list of all programming languages in the system.

    Parameters:
        request (Request): The raw request object (used for rate limiting).
        user (User): The authenticated user.
        session (Session): The database session dependency.

    Returns:
        Sequence[ProgrammingLanguage]: A list of all programming language objects.
    """
    return plang_service.get_programming_languages(session)


@plang_router.get("/count")
@limiter.limit("60/minute")
async def get_programming_language_count(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> int:
    """
    Retrieve the total number of programming languages in the system.

    Parameters:
        request (Request): The raw request object.
        user (User): The authenticated user.
        session (Session): The database session dependency.

    Returns:
        int: The total count of programming languages.
    """
    return len(plang_service.get_programming_languages(session))


@plang_router.get("/{id}")
@limiter.limit("60/minute")
async def get_programming_language(
    request: Request,
    id: str = Path(..., title="Programming Language ID"),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ProgrammingLanguage:
    """
    Retrieve a programming language by its ID.

    Parameters:
        request (Request): The raw request object.
        id (str): The ID of the programming language to retrieve.
        user (User): The authenticated user.
        session (Session): The database session dependency.

    Returns:
        ProgrammingLanguage: The programming language object with the given ID.

    Raises:
        HTTPException(404): If the programming language is not found.
    """
    plang = plang_service.get_programming_language_by_id(session, id)
    if not plang:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programming Language not found",
        )
    return plang


@plang_router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_programming_language(
    request: Request,
    payload: ProgrammingLanguageRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ProgrammingLanguage:
    """
    Create a new programming language (Admin only).

    Parameters:
        request (Request): The raw request object.
        payload (ProgrammingLanguageRequest): The payload containing the name.
        user (User): The authenticated user.
        session (Session): The database session dependency.

    Returns:
        ProgrammingLanguage: The newly created programming language object.

    Raises:
        HTTPException(403): If the user is not an admin.
        HTTPException(409): If a programming language with the same name already exists.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this endpoint",
        )

    existing = plang_service.get_programming_language_by_name(session, payload.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Programming Language with name '{payload.name}' already exists",
        )

    return plang_service.create_programming_language(session, payload.name, user.id)


@plang_router.put("/{id}")
@limiter.limit("10/minute")
async def update_programming_language(
    request: Request,
    payload: ProgrammingLanguageRequest,
    id: str = Path(..., title="Programming Language ID"),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> ProgrammingLanguage:
    """
    Update an existing programming language (Admin only).

    Parameters:
        request (Request): The raw request object.
        payload (ProgrammingLanguageRequest): The payload containing the new name.
        id (str): The ID of the programming language to update.
        user (User): The authenticated user.
        session (Session): The database session dependency.

    Returns:
        ProgrammingLanguage: The updated programming language object.

    Raises:
        HTTPException(403): If the user is not an admin.
        HTTPException(404): If the programming language is not found.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this endpoint",
        )

    plang = plang_service.get_programming_language_by_id(session, id)
    if not plang:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programming Language not found",
        )

    return plang_service.update_programming_language(session, plang, payload.name)


@plang_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_programming_language(
    request: Request,
    id: str = Path(..., title="Programming Language ID"),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> None:
    """
    Delete a programming language (Admin only).

    Parameters:
        request (Request): The raw request object.
        id (str): The ID of the programming language to delete.
        user (User): The authenticated user.
        session (Session): The database session dependency.

    Returns:
        None

    Raises:
        HTTPException(403): If the user is not an admin.
        HTTPException(404): If the programming language is not found.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this endpoint",
        )

    plang = plang_service.get_programming_language_by_id(session, id)
    if not plang:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Programming Language not found",
        )

    plang_service.delete_programming_language(session, plang)
    return None
