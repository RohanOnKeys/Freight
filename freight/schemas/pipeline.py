from datetime import datetime

from pydantic import BaseModel


class PipelineCreate(BaseModel):
    repo: str
    commit_sha: str
    branch: str


class PipelineOut(BaseModel):
    id: int
    repo: str
    commit_sha: str
    branch: str
    status: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }