from typing import Sequence

from sqlmodel import Session, select, or_

from src.entities.university_course import UniversityCourse


def get_courses(session: Session) -> Sequence[UniversityCourse]:
    """
    Retrieve all courses.

    Parameters:
        session (Session): The database session dependency.

    Returns:
        Sequence[UniversityCourse]: A list of all course objects.
    """
    return session.exec(select(UniversityCourse)).all()


def get_course_by_id(session: Session, id: str) -> UniversityCourse | None:
    """
    Retrieve a course by its ID.

    Parameters:
        session (Session): The database session dependency.
        id (str): The ID of the course to retrieve.

    Returns:
        UniversityCourse: The course object with the given ID.
    """
    return session.exec(
        select(UniversityCourse).where(UniversityCourse.id == id)
    ).first()


def get_course_by_name_or_code(
    session: Session, name: str, code: str
) -> UniversityCourse | None:
    """
    Retrieve a course by its name or code.

    Parameters:
        session (Session): The database session dependency.
        name (str): The name of the course to retrieve.
        code (str): The code of the course to retrieve.

    Returns:
        UniversityCourse: The course object with the given name or code.
    """
    statement = select(UniversityCourse).where(
        or_(UniversityCourse.name == name, UniversityCourse.code == code)
    )
    return session.exec(statement).first()


def create_course(session: Session, name: str, code: str) -> UniversityCourse:
    """
    Create a new course.

    Parameters:
        session (Session): The database session dependency.
        name (str): The name of the course to create.
        code (str): The code of the course to create.

    Returns:
        UniversityCourse: The newly created course object.
    """
    course = UniversityCourse(name=name, code=code)
    session.add(course)
    session.commit()
    session.refresh(course)
    return course


def update_course(
    session: Session, course: UniversityCourse, name: str | None, code: str | None
) -> UniversityCourse:
    """
    Update an existing course.

    Parameters:
        session (Session): The database session dependency.
        course (UniversityCourse): The course to update.
        name (str | None): The new name of the course.
        code (str | None): The new code of the course.

    Returns:
        UniversityCourse: The updated course object.
    """
    if name is not None:
        course.name = name
    if code is not None:
        course.code = code

    session.add(course)
    session.commit()
    session.refresh(course)
    return course


def delete_course(session: Session, course: UniversityCourse) -> None:
    """
    Delete a course.

    Parameters:
        session (Session): The database session dependency.
        course (UniversityCourse): The course to delete.
    """
    session.delete(course)
    session.commit()
