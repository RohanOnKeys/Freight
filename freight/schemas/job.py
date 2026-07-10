from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class JobOut(BaseModel):
    id: int
    pipeline_id: int
    name: str
    stage: str
    status: str
    needs: list[str]
    runner_id: Optional[int]
    exit_code: Optional[int]
    started_at: Optional[datetime]
    finished_at: Optional[datetime]

    model_config = {
        "from_attributes": True,
    }


class JobCompleteIn(BaseModel):
    status: str
    exit_code: int