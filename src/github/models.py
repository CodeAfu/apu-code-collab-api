from pydantic import BaseModel


class GitHubLinkRequest(BaseModel):
    code: str


class PaginatedRepoResponse(BaseModel):
    items: list[dict]
    size: int
    page: int
    has_next: bool


class AddSkillsRequest(BaseModel):
    skills: list[str]


class UpdateRepoDescriptionRequest(BaseModel):
    description: str
