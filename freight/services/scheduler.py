from sqlalchemy.orm import Session

from freight.models.job import Job
from freight.services.queue import push_job


def on_job_complete(
    db: Session,
    job_id: int,
    status: str = "completed",
) -> None:
    """
    Mark a job complete (or failed) and queue any newly-unblocked jobs.
    """

    completed_job = (
        db.query(Job)
        .filter(Job.id == job_id)
        .first()
    )

    if completed_job is None:
        raise ValueError(f"Job {job_id} not found")

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