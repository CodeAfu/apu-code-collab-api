from sqlmodel import Session, select

from src.entities.university_course import UniversityCourse


def get_university_courses(session: Session):
    return session.exec(select(UniversityCourse)).all()
