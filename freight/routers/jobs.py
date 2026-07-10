from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from freight.db.session import get_db
from freight.models.job import Job
from freight.schemas.job import JobOut

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
)


@router.get(
    "/{job_id}",
    response_model=JobOut,
)
def get_job(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve a single job by its identifier.

    Returns the current execution state and metadata of the job.
    """

    job = (
        db.query(Job)
        .filter(Job.id == job_id)
        .first()
    )

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    return job