from typing import Sequence

from fastapi import APIRouter, Depends, Request, Path, HTTPException, status
from sqlmodel import Session, SQLModel

from src.database.core import get_session
from src.entities.framework import Framework
from src.frameworks import service as fwork_service
from src.rate_limiter import limiter
from src.entities.user import User
from src.auth.service import get_current_user
from src.frameworks.models import FrameworkRequest

fwork_router = APIRouter(
    prefix="/api/v1/frameworks",
)


@fwork_router.get("/")
@limiter.limit("60/minute")
async def get_frameworks(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Sequence[Framework]:
    """
    Retrieve a list of all frameworks in the system.

    Returns:
        Sequence[Framework]: A list of all frameworks in the system.
    """
    return fwork_service.get_frameworks(session)


@fwork_router.get("/count")
@limiter.limit("60/minute")
async def get_framework_count(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> int:
    """
    Retrieve the total number of frameworks in the system.

    Returns:
        int: The total number of frameworks in the system.
    """
    return len(fwork_service.get_frameworks(session))


@fwork_router.get("/{id}")
@limiter.limit("60/minute")
async def get_framework(
    request: Request,
    id: str = Path(..., title="Framework ID"),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Framework:
    """
    Retrieve a framework by its ID.

    Parameters:
        id (str): The ID of the framework to retrieve.

    Returns:
        Framework: The framework object with the given ID.

    Raises:
        HTTPException(404): If no framework is found with the provided ID.
    """
    framework = fwork_service.get_framework_by_id(session, id)
    if not framework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Framework not found"
        )
    return framework


@fwork_router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_framework(
    request: Request,
    payload: FrameworkRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Framework:
    """
    Create a new framework (Admin only).

    Parameters:
        payload (FrameworkRequest): The payload containing the framework's name.
        user (User): The authenticated user.
        session (Session): The database session dependency.

    Returns:
        Framework: The newly created framework object.

    Raises:
        HTTPException(403): If the user is not an admin.
        HTTPException(409): If a framework with the same name already exists.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this endpoint",
        )

    # Check for duplicates
    existing = fwork_service.get_framework_by_name(session, payload.name)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Framework with name '{payload.name}' already exists",
        )

    return fwork_service.create_framework(session, payload.name, user.id)


@fwork_router.put("/{id}")
@limiter.limit("10/minute")
async def update_framework(
    request: Request,
    payload: FrameworkRequest,
    id: str = Path(..., title="Framework ID"),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Framework:
    """
    Update an existing framework (Admin only).

    Parameters:
        payload (FrameworkRequest): The payload containing the updated framework's name.
        id (str): The ID of the framework to update.
        user (User): The authenticated user.
        session (Session): The database session dependency.

    Returns:
        Framework: The updated framework object.

    Raises:
        HTTPException(403): If the user is not an admin.
        HTTPException(404): If no framework is found with the provided ID.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this endpoint",
        )

    framework = fwork_service.get_framework_by_id(session, id)
    if not framework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Framework not found"
        )

    return fwork_service.update_framework(session, framework, payload.name)


@fwork_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_framework(
    request: Request,
    id: str = Path(..., title="Framework ID"),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    """
    Delete a framework (Admin only).

    Parameters:
        id (str): The ID of the framework to delete.
        user (User): The authenticated user.
        session (Session): The database session dependency.

    Raises:
        HTTPException(403): If the user is not an admin.
        HTTPException(404): If no framework is found with the provided ID.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this endpoint",
        )

    framework = fwork_service.get_framework_by_id(session, id)
    if not framework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Framework not found"
        )

    fwork_service.delete_framework(session, framework)
    return None
