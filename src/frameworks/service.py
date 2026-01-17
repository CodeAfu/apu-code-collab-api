from typing import Sequence

from sqlmodel import Session, select

from src.entities.framework import Framework


def get_frameworks(session: Session) -> Sequence[Framework]:
    """
    Retrieve all frameworks from the database.

    Parameters:
        session (Session): The database session.

    Returns:
        Sequence[Framework]: A list of all Framework entities.
    """
    return session.exec(select(Framework)).all()


def get_framework_by_name(session: Session, name: str) -> Framework | None:
    """
    Retrieve a framework by its name.

    Parameters:
        session (Session): The database session.
        name (str): The name of the framework to search for.

    Returns:
        Framework | None: The framework entity if found, otherwise None.
    """
    return session.exec(select(Framework).where(Framework.name == name)).first()


def get_framework_by_id(session: Session, id: str) -> Framework | None:
    """
    Retrieve a framework by its ID.

    Parameters:
        session (Session): The database session.
        id (str): The ID of the framework to search for.

    Returns:
        Framework | None: The framework entity if found, otherwise None.
    """
    return session.exec(select(Framework).where(Framework.id == id)).first()


def create_framework(session: Session, name: str, user_id: str | None) -> Framework:
    """
    Create a new framework.

    Parameters:
        session (Session): The database session.
        name (str): The name of the framework to create.
        user_id (str): The ID of the user who created the framework.

    Returns:
        Framework: The newly created framework.
    """
    framework = Framework(name=name, added_by=user_id)
    session.add(framework)
    session.commit()
    session.refresh(framework)
    return framework


def update_framework(
    session: Session, framework: Framework, new_name: str
) -> Framework:
    """
    Update a framework.

    Parameters:
        session (Session): The database session.
        framework (Framework): The framework to update.
        new_name (str): The new name of the framework.

    Returns:
        Framework: The updated framework.
    """
    framework.name = new_name
    session.add(framework)
    session.commit()
    session.refresh(framework)
    return framework


def delete_framework(session: Session, framework: Framework) -> None:
    """
    Delete a framework.

    Parameters:
        session (Session): The database session.
        framework (Framework): The framework to delete.
    """
    session.delete(framework)
    session.commit()
