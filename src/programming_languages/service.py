from typing import Sequence

from sqlmodel import Session, select

from src.entities.programming_language import ProgrammingLanguage


def get_programming_languages(session: Session) -> Sequence[ProgrammingLanguage]:
    """
    Retrieve all programming languages from the database.

    Parameters:
        session (Session): The database session.

    Returns:
        Sequence[ProgrammingLanguage]: A list of all ProgrammingLanguage entities.
    """
    return session.exec(select(ProgrammingLanguage)).all()


def get_programming_language_by_name(
    session: Session, name: str
) -> ProgrammingLanguage | None:
    """
    Retrieve a programming language by its name.

    Parameters:
        session (Session): The database session.
        name (str): The name of the programming language to search for.

    Returns:
        ProgrammingLanguage | None: The programming language entity if found, otherwise None.
    """
    return session.exec(
        select(ProgrammingLanguage).where(ProgrammingLanguage.name == name)
    ).first()


def get_programming_language_by_id(
    session: Session, id: str
) -> ProgrammingLanguage | None:
    """
    Retrieve a programming language by its ID.

    Parameters:
        session (Session): The database session.
        id (str): The ID of the programming language to search for.

    Returns:
        ProgrammingLanguage | None: The programming language entity if found, otherwise None.
    """
    return session.exec(
        select(ProgrammingLanguage).where(ProgrammingLanguage.id == id)
    ).first()


def create_programming_language(
    session: Session, name: str, user_id: str
) -> ProgrammingLanguage:
    """
    Create a new programming language.

    Parameters:
        session (Session): The database session.
        name (str): The name of the programming language to create.
        user_id (str): The ID of the user who created the programming language.

    Returns:
        ProgrammingLanguage: The newly created programming language.
    """
    plang = ProgrammingLanguage(name=name, added_by=user_id)
    session.add(plang)
    session.commit()
    session.refresh(plang)
    return plang


def update_programming_language(
    session: Session, plang: ProgrammingLanguage, new_name: str
) -> ProgrammingLanguage:
    """
    Update a programming language.

    Parameters:
        session (Session): The database session.
        plang (ProgrammingLanguage): The programming language to update.
        new_name (str): The new name of the programming language.

    Returns:
        ProgrammingLanguage: The updated programming language.
    """
    plang.name = new_name
    session.add(plang)
    session.commit()
    session.refresh(plang)
    return plang


def delete_programming_language(session: Session, plang: ProgrammingLanguage) -> None:
    """
    Delete a programming language.

    Parameters:
        session (Session): The database session.
        plang (ProgrammingLanguage): The programming language to delete.
    """
    session.delete(plang)
    session.commit()
