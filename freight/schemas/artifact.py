"""
Pydantic schemas for Freight job artifacts.
"""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ArtifactOut(BaseModel):
    """
    Serialized representation of a job artifact.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int
    job_id: int
    path: str
    size: int
    created_at: datetime