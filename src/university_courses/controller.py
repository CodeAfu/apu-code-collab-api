from typing import Sequence

from fastapi import APIRouter, Depends, Request, Path, HTTPException, status
from sqlmodel import Session

from src.database.core import get_session
from src.entities.university_course import UniversityCourse
from src.university_courses import service as course_service
from src.rate_limiter import limiter
from src.entities.user import User
from src.auth.service import get_current_user
from src.university_courses.models import UniversityCourseRequest

course_router = APIRouter(
    prefix="/api/v1/university_courses",
)


@course_router.get("/")
@limiter.limit("60/minute")
async def get_courses(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> Sequence[UniversityCourse]:
    """
    Retrieve a list of all university courses in the system.

    Parameters:
        request (Request): The raw request object.
        user (User): The authenticated user.
        session (Session): The database session dependency.

    Returns:
        Sequence[UniversityCourse]: A list of all course objects.
    """
    return course_service.get_courses(session)


@course_router.get("/count")
@limiter.limit("60/minute")
async def get_course_count(
    request: Request,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> int:
    """
    Retrieve the total number of university courses.

    Parameters:
        request (Request): The raw request object.
        user (User): The authenticated user.
        session (Session): The database session dependency.

    Returns:
        int: The total count of courses.
    """
    return len(course_service.get_courses(session))


@course_router.get("/{id}")
@limiter.limit("60/minute")
async def get_course(
    request: Request,
    id: str = Path(..., title="Course ID"),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> UniversityCourse:
    """
    Retrieve a university course by its ID.

    Parameters:
        request (Request): The raw request object.
        id (str): The ID of the course to retrieve.
        user (User): The authenticated user.
        session (Session): The database session dependency.

    Returns:
        UniversityCourse: The course object with the given ID.

    Raises:
        HTTPException(404): If the course is not found.
    """
    course = course_service.get_course_by_id(session, id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University Course not found",
        )
    return course


@course_router.post("/", status_code=status.HTTP_201_CREATED)
@limiter.limit("10/minute")
async def create_course(
    request: Request,
    payload: UniversityCourseRequest,
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> UniversityCourse:
    """
    Create a new university course (Admin only).

    Parameters:
        request (Request): The raw request object.
        payload (UniversityCourseRequest): The payload containing name and code.
        user (User): The authenticated user.
        session (Session): The database session dependency.

    Returns:
        UniversityCourse: The newly created course object.

    Raises:
        HTTPException(403): If the user is not an admin.
        HTTPException(409): If a course with the same name or code already exists.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this endpoint",
        )

    # Check for duplicates on Name OR Code
    existing = course_service.get_course_by_name_or_code(
        session, payload.name, payload.code
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Course with name '{payload.name}' or code '{payload.code}' already exists",
        )

    return course_service.create_course(session, payload.name, payload.code)


@course_router.put("/{id}")
@limiter.limit("10/minute")
async def update_course(
    request: Request,
    payload: UniversityCourseRequest,
    id: str = Path(..., title="Course ID"),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> UniversityCourse:
    """
    Update an existing university course (Admin only).

    Parameters:
        request (Request): The raw request object.
        payload (UniversityCourseRequest): The payload containing the new details.
        id (str): The ID of the course to update.
        user (User): The authenticated user.
        session (Session): The database session dependency.

    Returns:
        UniversityCourse: The updated course object.

    Raises:
        HTTPException(403): If the user is not an admin.
        HTTPException(404): If the course is not found.
        HTTPException(409): If the new name or code conflicts with another course.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this endpoint",
        )

    course = course_service.get_course_by_id(session, id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University Course not found",
        )

    # Check duplicate if name/code changed
    # Logic: if name matches existing but ID is different => Conflict
    # Simplified: Check if any OTHER course has this name/code
    potential_conflict = course_service.get_course_by_name_or_code(
        session, payload.name, payload.code
    )
    if potential_conflict and potential_conflict.id != course.id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Another course with name '{payload.name}' or code '{payload.code}' already exists",
        )

    return course_service.update_course(session, course, payload.name, payload.code)


@course_router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("10/minute")
async def delete_course(
    request: Request,
    id: str = Path(..., title="Course ID"),
    user: User = Depends(get_current_user),
    session: Session = Depends(get_session),
) -> None:
    """
    Delete a university course (Admin only).

    Parameters:
        request (Request): The raw request object.
        id (str): The ID of the course to delete.
        user (User): The authenticated user.
        session (Session): The database session dependency.

    Returns:
        None

    Raises:
        HTTPException(403): If the user is not an admin.
        HTTPException(404): If the course is not found.
    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not allowed to access this endpoint",
        )

    course = course_service.get_course_by_id(session, id)
    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="University Course not found",
        )

    course_service.delete_course(session, course)
    return None
