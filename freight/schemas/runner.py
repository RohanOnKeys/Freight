from datetime import datetime

from pydantic import BaseModel, ConfigDict


class RunnerRegisterIn(BaseModel):
    hostname: str


class RunnerOut(BaseModel):
    id: int
    hostname: str
    status: str
    last_heartbeat: datetime

    model_config = ConfigDict(from_attributes=True)