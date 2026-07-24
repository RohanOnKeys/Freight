"""
Job completion and scheduling logic for Freight pipelines.

This module is the single place where a job's terminal (or retried)
outcome is decided, and where downstream jobs are released once every
job they depend on has completed.
"""

from sqlalchemy.orm import Session

from freight.core.retry import handle_job_failure
from freight.models.job import Job
from freight.services.queue import push_job


def on_job_complete(
    db: Session,
    job_id: int,
    status: str = "completed",
) -> None:
    """
    Mark a job complete (or failed) and queue any newly-unblocked jobs.

    A failed job is not always terminal: if it still has retry attempts
    remaining (`Job.retries < Job.max_retries`, configured through the
    pipeline's `retries:` field), `freight.core.retry.handle_job_failure`
    transparently requeues it with an exponential backoff delay instead
    of finalizing it as `failed`. Downstream jobs stay blocked until the
    retry itself either succeeds or the retry budget is exhausted.

    Args:
        db:
            Active database session.

        job_id:
            Identifier of the job reporting its outcome.

        status:
            Final execution status reported by the runner
            (`"completed"` or `"failed"`).

    Raises:
        ValueError:
            If no job exists with the supplied identifier.
    """

    completed_job = (
        db.query(Job)
        .filter(Job.id == job_id)
        .first()
    )

    if completed_job is None:
        raise ValueError(f"Job {job_id} not found")

    print(
        f"[scheduler] status={status} "
        f"retries={completed_job.retries} "
        f"max={completed_job.max_retries}"
    )

    # A failed job with retry attempts left gets requeued instead of
    # finalized — stop here and leave downstream jobs blocked.
    if status == "failed" and handle_job_failure(db, completed_job):
        return

    completed_job.status = status
    db.commit()

    # Only unlock downstream jobs on success.
    if status != "completed":
        return

    schedule_pipeline(
        db,
        completed_job.pipeline_id,
    )


def schedule_pipeline(db: Session, pipeline_id: int) -> None:
    """
    Queue every job whose dependencies are already satisfied.

    Args:
        db:
            Active database session.

        pipeline_id:
            Identifier of the pipeline whose pending jobs should be
            evaluated for release.
    """

    jobs = (
        db.query(Job)
        .filter(Job.pipeline_id == pipeline_id)
        .all()
    )

    job_lookup = {
        job.name: job
        for job in jobs
    }

    for job in jobs:

        # Skip jobs already processed
        if job.status != "pending":
            continue

        ready = True
        needs = job.needs or []

        for dependency in needs:

            dependency_job = job_lookup.get(dependency)

            if dependency_job is None:
                ready = False
                break

            if dependency_job.status != "completed":
                ready = False
                break

        if ready:
            job.status = "queued"
            push_job(job.id)

    db.commit()