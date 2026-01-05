from pydantic import BaseModel


class GitHubLinkRequest(BaseModel):
    code: str


class GithubRepositoryStatsPayload(BaseModel):
    repository_language: str
    topics: list[str]
    forks_count: int
    stargazers_count: int
    subscribers_count: int
    open_issues_count: int


class PaginatedRepoResponse(BaseModel):
    items: list[dict]
    size: int
    page: int
    has_next: bool


class AddSkillsRequest(BaseModel):
    skills: list[str]


class UpdateRepoDescriptionRequest(BaseModel):
    description: str
