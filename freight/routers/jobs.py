"""
HTTP routes for Freight job operations.

This module exposes the API endpoints used to inspect and manage the
lifecycle of individual CI/CD jobs.

Supported operations include:

- Retrieving job state and execution metadata.
- Atomically claiming queued jobs for runner execution.
- Receiving incremental execution log chunks from runners.
- Recording final job completion status and exit codes.

Job claiming is protected by a conditional database update so that only
one runner can acquire ownership of a queued job. Execution logs are
persisted incrementally under the local ``logs/`` directory.

Business logic related to dependency resolution and downstream job
scheduling is delegated to the scheduler service.
"""

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Body, Depends, HTTPException, status
from sqlalchemy.orm import Session

from freight.db.session import get_db
from freight.models.job import Job
from freight.schemas.job import JobClaimIn, JobCompleteIn, JobOut
from freight.schemas.secret import JobSecretsOut
from freight.services.scheduler import on_job_complete
from freight.services.secret_service import resolve_job_secrets


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

    Returns the current execution state, pipeline association, assigned
    runner, dependency information, exit code, and execution timestamps.

    Raises:
        HTTPException: If no job exists with the supplied identifier.

    Returns:
        Job: The requested job database record, serialized through
        ``JobOut``.
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

    Ownership is granted through a conditional database update. The
    operation succeeds only when the requested job is still queued and
    has no existing runner assignment.

    This database-side guard prevents multiple runners from successfully
    claiming the same job during a concurrent race.

    Args:
        job_id: Identifier of the job being claimed.
        payload: Request containing the claiming runner's identifier.
        db: Active database session supplied by FastAPI.

    Raises:
        HTTPException: If the job has already been claimed or is no
        longer available for execution.

    Returns:
        dict: Confirmation of the successful runner assignment.
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
                Job.started_at: datetime.utcnow(),
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


@router.get(
    "/{job_id}/secrets",
    response_model=JobSecretsOut,
)
def get_job_secrets(
    job_id: int,
    db: Session = Depends(get_db),
) -> JobSecretsOut:
    """
    Retrieve decrypted execution secrets for a job.

    This endpoint is intended exclusively for authenticated Freight runners
    immediately before container execution.

    The returned secrets are injected into the execution container as
    environment variables and must never be persisted or exposed through
    public APIs.

    Args:
        job_id:
            Identifier of the Freight job.

        db:
            Active database session.

    Raises:
        HTTPException:
            If the requested job does not exist.

    Returns:
        Mapping of secret names to decrypted values required during job
        execution.
    """

    job = db.get(Job, job_id)

    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job not found.",
        )

    secrets = resolve_job_secrets(
        db=db,
        scope="global",
    )

    return JobSecretsOut(
        secrets=secrets,
    )


@router.post(
    "/{job_id}/logs",
    status_code=200,
)
def append_job_logs(
    job_id: int,
    chunk: str = Body(
        ...,
        media_type="text/plain",
    ),
    db: Session = Depends(get_db),
):
    """
    Append runner output to a job's persistent log file.

    Runners send execution output to this endpoint as plain-text chunks.
    Each chunk is appended to ``logs/{job_id}.log`` in the order in which
    it reaches the server.

    The logs directory is created automatically if it does not already
    exist.

    Args:
        job_id: Identifier of the job producing the output.
        chunk: Plain-text execution output received from the runner.
        db: Active database session supplied by FastAPI.

    Raises:
        HTTPException: If no job exists with the supplied identifier.

    Returns:
        dict: Confirmation that the log chunk was persisted.
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

    log_root = Path("logs")
    log_root.mkdir(
        parents=True,
        exist_ok=True,
    )

    log_path = log_root / f"{job_id}.log"

    with log_path.open(
        "a",
        encoding="utf-8",
    ) as log_file:
        log_file.write(chunk)

    return {
        "message": "Log chunk appended successfully",
        "job_id": job_id,
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
    Record the final execution result of a job.

    This endpoint is called by a runner after container execution has
    finished. The process exit code is stored and the scheduler service
    is notified of the resulting job status.

    The scheduler may then release downstream jobs whose dependencies
    have become satisfied.

    Args:
        job_id: Identifier of the completed job.
        payload: Final job status and container exit code.
        db: Active database session supplied by FastAPI.

    Raises:
        HTTPException: If no job exists with the supplied identifier.

    Returns:
        dict: Confirmation of the job's resulting execution state.
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
    job.finished_at = datetime.now(timezone.utc)

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