"""
Pipeline creation service.

Coordinates the creation of a Freight pipeline from a parsed pipeline
definition. This service is intended to be the single entry point used
by every ingestion source, including GitHub webhooks, the CLI, future
REST APIs, and manual triggers.
"""

from pathlib import Path

from sqlalchemy.orm import Session

from freight.models.pipeline import Pipeline
from freight.services.dag import build_dag, validate_dag
from freight.services.pipeline_loader import load_pipeline
from freight.services.pipeline_parser import parse_pipeline
from freight.services.scheduler import schedule_pipeline


def create_pipeline(
    db: Session,
    pipeline_file: str | Path,
) -> Pipeline:
    """
    Parse, validate, persist, and schedule a Freight pipeline.

    Args:
        db:
            Active database session.
        pipeline_file:
            Path to a .freight.yml file.

    Returns:
        The newly created Pipeline ORM object.
    """

    pipeline_definition = parse_pipeline(
        pipeline_file,
    )

    pipeline = Pipeline()

    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)

    load_pipeline(
        db=db,
        pipeline_id=pipeline.id,
        pipeline=pipeline_definition,
    )

    pipeline_graph = build_dag(pipeline_definition)
    validate_dag(pipeline_graph)

    schedule_pipeline(
        db=db,
        pipeline_id=pipeline.id,
    )

    return pipeline