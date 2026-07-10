from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from freight.db.session import get_db
from freight.models.pipeline import Pipeline
from freight.schemas.pipeline import PipelineOut

router = APIRouter(
    prefix="/pipelines",
    tags=["Pipelines"],
)


@router.get(
    "/{pipeline_id}",
    response_model=PipelineOut,
)
def get_pipeline(
    pipeline_id: int,
    db: Session = Depends(get_db),
):
    pipeline = (
        db.query(Pipeline)
        .options(selectinload(Pipeline.jobs))
        .filter(Pipeline.id == pipeline_id)
        .first()
    )

    if pipeline is None:
        raise HTTPException(
            status_code=404,
            detail="Pipeline not found",
        )

    return pipeline