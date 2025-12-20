from loguru import logger
from sqlmodel import Session, SQLModel, create_engine

from src.config import settings

from src.entities import user, refresh_token, github_repository  # noqa

if settings.is_development:
    logger.debug(f"DATABASE_URL={settings.DATABASE_URL}")

engine = create_engine(settings.DATABASE_URL, echo=True)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
