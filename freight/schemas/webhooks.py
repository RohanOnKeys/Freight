from pydantic import BaseModel


class Repository(BaseModel):
    name: str


class GitHubWebhook(BaseModel):
    ref: str
    after: str
    repository: Repository