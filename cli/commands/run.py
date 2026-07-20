from pathlib import Path
import sys

from freight.db.session import SessionLocal
from freight.services.pipeline_services import create_pipeline


def run_command(args):
    """
    Execute a local Freight pipeline.

    This command only performs CLI responsibilities:
        - Validate the pipeline file exists.
        - Open a database session.
        - Delegate pipeline creation to the shared service.
        - Commit or rollback the transaction.
        - Display the result.

    All pipeline parsing, DAG validation, job creation,
    scheduling, and queueing are handled by
    freight.services.pipeline_services.create_pipeline().
    """

    pipeline_file = Path(args.pipeline)

    if not pipeline_file.exists():
        print(f"Error: '{pipeline_file}' does not exist.")
        sys.exit(1)

    db = SessionLocal()

    try:
        pipeline = create_pipeline(
            db=db,
            pipeline_file=pipeline_file,
            source="local",
            repo=None,
            branch=None,
            commit_sha=None,
        )

        db.commit()

        print("✓ Pipeline created successfully")
        print(f"Pipeline ID : {pipeline.id}")
        print(f"Source      : {pipeline.source}")

    except Exception as exc:
        db.rollback()
        print(f"Error: {exc}")
        sys.exit(1)

    finally:
        db.close()