from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from freight.core.security import verify_github_signature
from freight.db.session import get_db
from freight.models.pipeline import Pipeline
from freight.schemas.pipeline import PipelineOut

router = APIRouter(
    prefix="/webhook",
    tags=["Webhooks"],
)


@router.post("/", response_model=PipelineOut, status_code=201)
async def receive_webhook(
    request: Request,
    db: Session = Depends(get_db),
):
    payload = await request.body()

    signature = request.headers.get(
        "X-Hub-Signature-256"
    )

    if not verify_github_signature(
        payload,
        signature,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid signature",
        )

    data = await request.json()

    repo = data["repository"]["name"]
    branch = data["ref"].split("/")[-1]
    commit_sha = data["after"]

    pipeline = Pipeline(
        repo=repo,
        commit_sha=commit_sha,
        branch=branch,
        status="pending",
    )

    db.add(pipeline)
    db.commit()
    db.refresh(pipeline)

    return pipeline