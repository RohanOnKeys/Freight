"""
GitHub webhook endpoints.

Receives GitHub webhook events, verifies their authenticity, extracts
repository metadata, fetches the exact `.freight.yml` that existed in
the pushed repository at the pushed commit, and delegates pipeline
creation to the pipeline service.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from freight.core.security import verify_github_signature
from freight.db.session import get_db
from freight.schemas.pipeline import PipelineOut
from freight.schemas.webhooks import GitHubWebhook
from freight.services.github_client import (
    GitHubFetchError,
    PipelineFileNotFoundError,
    fetch_pipeline_file,
)
from freight.services.pipeline_services import create_pipeline

router = APIRouter(
    prefix="/webhook",
    tags=["Webhooks"],
)

PIPELINE_FILE_PATH = ".freight.yml"
"""Path, relative to the repository root, of the Freight pipeline file."""


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
    extracting repository metadata. The `.freight.yml` pipeline
    definition is then fetched directly from GitHub's Contents API at
    the exact commit that was pushed, so pipeline behavior always
    matches the code that triggered it rather than any file that
    happens to exist on the Freight server itself. Pipeline creation,
    validation, scheduling, and job creation are delegated to the
    pipeline service.

    Raises:
        HTTPException(401):
            If the request's HMAC signature does not match.

        HTTPException(422):
            If the pushed repository has no `.freight.yml` at the
            pushed commit.

        HTTPException(502):
            If the GitHub API could not be reached, or returned an
            unexpected response, while fetching the pipeline file.
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

    branch = data.ref.split("/")[-1]

    try:
        pipeline_content = fetch_pipeline_file(
            repo_full_name=data.repository.full_name,
            commit_sha=data.after,
            path=PIPELINE_FILE_PATH,
        )
    except PipelineFileNotFoundError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except GitHubFetchError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc),
        ) from exc

    pipeline = create_pipeline(
        db=db,
        pipeline_content=pipeline_content,
        source="github",
        repo=data.repository.full_name,
        branch=branch,
        commit_sha=data.after,
    )

    return pipeline