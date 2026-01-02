from typing import Sequence

from fastapi import APIRouter, Depends, Request
from loguru import logger
from sqlmodel import Session

from src.database.core import get_session
from src.entities.university_course import UniversityCourse
from src.rate_limiter import limiter
from src.university_courses import service as university_course_service

university_course_router = APIRouter(
    prefix="/api/v1/university_courses",
)


@university_course_router.get(
    "/",
)
@limiter.limit("20/minute")
async def get_university_courses(
    request: Request,
    session: Session = Depends(get_session),
) -> Sequence[UniversityCourse]:
    """
    Retrieve a list of all university courses in the system.

    Parameters:
        session (Session): The database session dependency.

    Returns:
        Sequence[UniversityCourse]: A list of all university course objects stored in the database.
    """
    courses = university_course_service.get_university_courses(session)
    logger.info(f"Retrieved {len(courses)} university courses")
    return courses
