"""
HTTP routes for Freight job artifacts.

Artifacts are files generated during job execution that should remain
available after the job has finished. They are uploaded by runners,
stored on the Freight server, and indexed in the database so they can
later be listed or downloaded.
"""

from pathlib import Path
import shutil

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from sqlalchemy.orm import Session

from freight.core.config import settings
from freight.db.session import get_db
from freight.models.artifact import Artifact
from freight.models.job import Job
from freight.schemas.artifact import ArtifactOut


router = APIRouter(
    tags=["Artifacts"],
)


@router.post(
    "/jobs/{job_id}/artifacts",
    response_model=ArtifactOut,
    status_code=201,
)
def upload_artifact(
    job_id: int,
    path: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a job artifact.

    Stores the uploaded file beneath the configured artifact root using
    the following directory layout:

        ARTIFACT_ROOT/
            pipeline_id/
                job_id/
                    relative/path/to/file

    The original relative workspace path is preserved so directory
    structure is maintained.

    Args:
        job_id:
            Identifier of the job that produced the artifact.
        path:
            Relative artifact path inside the job workspace.
        file:
            Uploaded artifact file.
        db:
            Active database session supplied by FastAPI.

    Raises:
        HTTPException:
            If the requested job does not exist.

    Returns:
        Artifact:
            Newly created artifact database record.
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

    artifact_dir = (
        Path(settings.ARTIFACT_ROOT)
        / str(job.pipeline_id)
        / str(job.id)
    )

    artifact_path = artifact_dir / path

    artifact_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with artifact_path.open("wb") as buffer:
        shutil.copyfileobj(
            file.file,
            buffer,
        )

    artifact = Artifact(
        job_id=job.id,
        path=str(artifact_path),
        size=artifact_path.stat().st_size,
    )

    db.add(artifact)
    db.commit()
    db.refresh(artifact)

    return artifact


@router.get(
    "/jobs/{job_id}/artifacts",
    response_model=list[ArtifactOut],
)
def list_artifacts(
    job_id: int,
    db: Session = Depends(get_db),
):
    """
    Retrieve every artifact produced by a job.

    Args:
        job_id:
            Identifier of the completed job.
        db:
            Active database session supplied by FastAPI.

    Raises:
        HTTPException:
            If the requested job does not exist.

    Returns:
        list[Artifact]:
            Every artifact associated with the supplied job.
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

    artifacts = (
        db.query(Artifact)
        .filter(Artifact.job_id == job_id)
        .all()
    )

    return artifacts