from loguru import logger
from sqlmodel import Session, SQLModel, create_engine

from src.config import settings
from src.entities import github_repository, refresh_token, user  # noqa

if settings.is_development:
    logger.debug(f"DATABASE_URL={settings.DATABASE_URL}")

engine = create_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
    pool_recycle=3600,
)


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
