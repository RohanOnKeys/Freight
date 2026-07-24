"""
Pydantic schemas for Freight job API operations.

Defines the request and response models used when retrieving jobs,
claiming queued work, and reporting job completion.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JobOut(BaseModel):
    """
    Response schema representing a Freight job.

    Includes the job's pipeline association, execution configuration,
    dependency information, assigned runner, result, timestamps, and
    the source repository/branch/commit the runner should check out
    before execution. `repo`, `branch`, and `commit_sha` are populated
    only for jobs whose pipeline originated from a GitHub webhook;
    they are `None` for pipelines submitted through the local CLI.
    """

    id: int
    pipeline_id: int
    name: str
    stage: str
    status: str
    needs: list[str]
    image: str
    script: list[str]
    artifacts_config: dict
    runner_id: Optional[int]
    retries: int
    max_retries: int
    exit_code: Optional[int]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

    repo: Optional[str] = None
    branch: Optional[str] = None
    commit_sha: Optional[str] = None

    model_config = {
        "from_attributes": True,
    }


class JobCompleteIn(BaseModel):
    """
    Request payload for reporting job completion.

    Sent by a runner after execution finishes to report the final status
    and process exit code.
    """

    status: str
    exit_code: int


class JobClaimIn(BaseModel):
    """
    Request payload for claiming a queued job.

    Identifies the runner attempting to acquire ownership of the job.
    """

    runner_id: int