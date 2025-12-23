from pydantic import BaseModel


class GitHubLinkRequest(BaseModel):
    code: str
