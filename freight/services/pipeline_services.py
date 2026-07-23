"""
Pipeline creation service.

Coordinates the creation of a Freight pipeline from a parsed pipeline
definition. This service is the single ingestion entry point used by
GitHub webhooks, the local CLI, and future ingestion mechanisms such as
REST APIs, scheduled executions, and manual triggers.

Exactly one of `pipeline_file` or `pipeline_content` must be supplied:

* `pipeline_file` is used by the local CLI, where the pipeline
  definition is a real path on disk.
* `pipeline_content` is used by the GitHub webhook, where the pipeline
  definition was already fetched from GitHub's Contents API at the
  exact pushed commit and is passed in as raw YAML text.
"""

from pathlib import Path

from sqlalchemy.orm import Session

from freight.models.pipeline import Pipeline
from freight.services.dag import build_dag, validate_dag
from freight.services.pipeline_loader import load_pipeline
from freight.services.pipeline_parser import parse_pipeline, parse_pipeline_text
from freight.services.scheduler import schedule_pipeline


def create_pipeline(
    db: Session,
    pipeline_file: str | Path | None = None,
    pipeline_content: str | None = None,
    *,
    source: str,
    repo: str | None = None,
    branch: str | None = None,
    commit_sha: str | None = None,
) -> Pipeline:
    """
    Parse, validate, persist, and schedule a Freight pipeline.

    Args:
        db:
            Active database session.

        pipeline_file:
            Path to a local Freight pipeline definition. Used by the
            CLI. Mutually exclusive with `pipeline_content`.

        pipeline_content:
            Raw YAML text of a Freight pipeline definition, already
            fetched from its source (for example, GitHub's Contents
            API at a specific commit). Used by the webhook ingestion
            path. Mutually exclusive with `pipeline_file`.

        source:
            Origin of the pipeline (for example: github or local).

        repo:
            Repository name, if applicable.

        branch:
            Git branch name, if applicable.

        commit_sha:
            Commit SHA associated with the pipeline, if applicable.

    Returns:
        The newly created Pipeline ORM object.

    Raises:
        ValueError:
            If neither or both of `pipeline_file` and
            `pipeline_content` are supplied.
    """

    if (pipeline_file is None) == (pipeline_content is None):
        raise ValueError(
            "create_pipeline requires exactly one of "
            "'pipeline_file' or 'pipeline_content'."
        )

    if pipeline_content is not None:
        pipeline_definition = parse_pipeline_text(
            pipeline_content,
        )
    else:
        pipeline_definition = parse_pipeline(
            pipeline_file,
        )

    pipeline = Pipeline(
        source=source,
        repo=repo,
        branch=branch,
        commit_sha=commit_sha,
        status="pending",
    )

    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)

    load_pipeline(
        db=db,
        pipeline_id=pipeline.id,
        pipeline=pipeline_definition,
    )

    pipeline_graph = build_dag(
        pipeline_definition,
    )
    validate_dag(
        pipeline_graph,
    )

    schedule_pipeline(
        db=db,
        pipeline_id=pipeline.id,
    )

    db.refresh(pipeline)

    return pipeline