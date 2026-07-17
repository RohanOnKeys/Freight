"""Pipeline request and response schemas."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from freight.schemas.job import JobOut


class PipelineCreate(BaseModel):
    """Schema for creating a new pipeline request."""

    source: str

    repo: str | None = None
    commit_sha: str | None = None
    branch: str | None = None


class PipelineOut(BaseModel):
    """Schema for representing pipeline data returned by the API."""

    id: int
    source: str

    repo: str | None = None
    commit_sha: str | None = None
    branch: str | None = None

    status: str
    created_at: datetime

    jobs: list[JobOut] = []

    model_config = ConfigDict(
        from_attributes=True,
    )