from datetime import datetime

from pydantic import BaseModel

from freight.schemas.job import JobOut


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

    jobs: list[JobOut] = []

    model_config = {
        "from_attributes": True
    }