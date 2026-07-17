from sqlalchemy.orm import Session

from freight.models.job import Job


def load_pipeline(
    db: Session,
    pipeline_id: int,
    pipeline: dict,
) -> None:
    """
    Load parsed pipeline jobs into the database.

    Each job defined in the pipeline is converted into a Job ORM object.
    Dependency information and artifact configuration are normalized
    before being persisted.
    """

    jobs = pipeline.get("jobs", {})

    for job_name, config in jobs.items():

        needs = config.get("needs", [])

        if isinstance(needs, str):
            needs = [needs]

        artifacts_config = config.get(
            "artifacts",
            {},
        )

        job = Job(
            pipeline_id=pipeline_id,
            name=job_name,
            stage=config.get("stage"),
            status="pending",
            needs=needs,
            image=config.get("image"),
            script=config.get("script", []),
            artifacts_config=artifacts_config,
        )

        db.add(job)

    db.commit()