from sqlmodel import SQLModel


class FrameworkRequest(SQLModel):
    name: str
