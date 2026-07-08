from pydantic import BaseModel


class Repository(BaseModel):
    name: str


class GitHubWebhook(BaseModel):
    ref: str
    repository: Repository