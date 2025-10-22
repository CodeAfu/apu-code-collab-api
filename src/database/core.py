from sqlmodel import create_engine, SQLModel, Session
from src.config import settings

if settings.is_development:
    print(f"DATABASE_URL={settings.DATABASE_URL}")

engine = create_engine(settings.DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session