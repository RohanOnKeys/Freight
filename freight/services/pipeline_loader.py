from sqlalchemy.orm import Session

from freight.models.job import Job


def load_pipeline(
    db: Session,
    pipeline_id: int,
    pipeline: dict,
):
    jobs = pipeline.get("jobs", {})

    for job_name, config in jobs.items():

        needs = config.get("needs", [])

        if isinstance(needs, str):
            needs = [needs]

        job = Job(
            pipeline_id=pipeline_id,
            name=job_name,
            stage=config.get("stage"),
            status="pending",
            needs=needs,
            image=config.get("image"),
            script=config.get("script", []),
        )

        db.add(job)

    db.commit()