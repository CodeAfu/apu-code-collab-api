from pydantic import BaseModel


class UniversityCourseRequest(BaseModel):
    name: str
    code: str
