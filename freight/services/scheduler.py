from sqlalchemy.orm import Session

from freight.models.job import Job
from freight.services.queue import push_job


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

        for dependency in job.needs:

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