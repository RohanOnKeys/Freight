"""
GitHub webhook endpoints.

Receives GitHub webhook events, verifies their authenticity, extracts
repository metadata, and delegates pipeline creation to the pipeline
service.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from freight.core.security import verify_github_signature
from freight.db.session import get_db
from freight.schemas.pipeline import PipelineOut
from freight.schemas.webhooks import GitHubWebhook
from freight.services.pipeline_services import create_pipeline

router = APIRouter(
    prefix="/webhook",
    tags=["Webhooks"],
)


@router.post(
    "/",
    response_model=PipelineOut,
    status_code=201,
)
async def receive_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Receive a GitHub webhook and create a Freight pipeline.

    The webhook is authenticated using GitHub's HMAC signature before
    extracting repository metadata. Pipeline creation, validation,
    scheduling, and job creation are delegated to the pipeline service.
    """

    payload = await request.body()

    signature = request.headers.get(
        "X-Hub-Signature-256",
    )

    if not verify_github_signature(
        payload,
        signature,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid signature",
        )

    data = GitHubWebhook.model_validate_json(
        payload,
    )

    pipeline = create_pipeline(
        db=db,
        pipeline_file=".freight.yml",
        source="github",
        repo=data.repository.name,
        branch=data.ref.split("/")[-1],
        commit_sha=data.after,
    )

    return pipeline