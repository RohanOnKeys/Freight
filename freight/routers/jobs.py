"""
HTTP routes for Freight job operations.

Provides endpoints for retrieving jobs, atomically claiming queued work,
and reporting job completion.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from freight.db.session import get_db
from freight.models.job import Job
from freight.schemas.job import JobClaimIn, JobCompleteIn, JobOut
from freight.services.scheduler import on_job_complete


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
    Retrieve a job by its identifier.

    Returns the current execution state, assigned runner, dependency
    information, and execution metadata for the requested job.
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


@router.post(
    "/{job_id}/claim",
    status_code=200,
)
def claim_job(
    job_id: int,
    payload: JobClaimIn,
    db: Session = Depends(get_db),
):
    """
    Atomically assign a queued job to a runner.

    The conditional database update succeeds only when the job is still
    queued and has no assigned runner. This prevents concurrent runners
    from successfully claiming the same job.
    """

    updated_rows = (
        db.query(Job)
        .filter(
            Job.id == job_id,
            Job.status == "queued",
            Job.runner_id.is_(None),
        )
        .update(
            {
                Job.status: "running",
                Job.runner_id: payload.runner_id,
            },
            synchronize_session=False,
        )
    )

    if updated_rows == 0:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Job is not available for claiming",
        )

    db.commit()

    return {
        "message": "Job claimed successfully",
        "job_id": job_id,
        "runner_id": payload.runner_id,
        "status": "running",
    }


@router.post(
    "/{job_id}/complete",
    status_code=200,
)
def complete_job(
    job_id: int,
    payload: JobCompleteIn,
    db: Session = Depends(get_db),
):
    """
    Mark a job as completed or failed.

    Invoked by a runner after execution finishes. The final execution
    state is recorded and the scheduler is notified so that downstream
    jobs whose dependencies are satisfied can be released.
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

    job.exit_code = payload.exit_code

    on_job_complete(
        db=db,
        job_id=job_id,
        status=payload.status,
    )

    db.refresh(job)

    return {
        "message": "Job updated successfully",
        "status": job.status,
    }