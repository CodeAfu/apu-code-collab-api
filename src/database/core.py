import os
from dotenv import load_dotenv
from sqlmodel import create_engine, SQLModel, Session

load_dotenv()

PYTHON_ENV = os.getenv("PYTHON_ENV")
DATABASE_URL = os.getenv("DATABASE_URL")

if PYTHON_ENV == "development":
    print(f"DATABASE_URL={DATABASE_URL}")

engine = create_engine(DATABASE_URL, echo=True)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session