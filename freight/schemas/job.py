from datetime import datetime

from pydantic import BaseModel


class JobOut(BaseModel):
    id: int
    pipeline_id: int
    name: str
    stage: str
    status: str
    runner_id: int | None
    exit_code: int | None
    started_at: datetime | None
    finished_at: datetime | None

    model_config = {
        "from_attributes": True
    }