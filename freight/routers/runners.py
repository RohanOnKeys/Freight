"""
HTTP routes for Freight runner registration and health reporting.

Runners register with a unique hostname and periodically send heartbeats
to indicate that they are alive. Re-registering an existing hostname
reactivates the existing runner record instead of creating a duplicate.
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from freight.db.session import get_db
from freight.models.runner import Runner
from freight.schemas.runner import RunnerOut, RunnerRegisterIn


router = APIRouter(
    prefix="/runners",
    tags=["Runners"],
)


@router.post(
    "/register",
    response_model=RunnerOut,
    status_code=200,
)
def register_runner(
    payload: RunnerRegisterIn,
    db: Session = Depends(get_db),
) -> Runner:
    """
    Register a new runner or reactivate an existing runner.

    Runner hostnames are unique. If a runner with the supplied hostname
    already exists, its existing database identity is reused and its
    health state is refreshed.

    Args:
        payload: Registration data containing the runner hostname.
        db: Active database session supplied by FastAPI.

    Returns:
        The newly created or reactivated runner record.
    """

    now = datetime.now(timezone.utc)

    runner = (
        db.query(Runner)
        .filter(Runner.hostname == payload.hostname)
        .first()
    )

    if runner is None:
        runner = Runner(
            hostname=payload.hostname,
            status="alive",
            last_heartbeat=now,
        )
        db.add(runner)
    else:
        runner.status = "alive"
        runner.last_heartbeat = now

    db.commit()
    db.refresh(runner)

    return runner


@router.post(
    "/{runner_id}/heartbeat",
    response_model=RunnerOut,
)
def heartbeat(
    runner_id: int,
    db: Session = Depends(get_db),
) -> Runner:
    """
    Refresh the health state of a registered runner.

    Args:
        runner_id: Identifier of the runner sending the heartbeat.
        db: Active database session supplied by FastAPI.

    Raises:
        HTTPException: If the requested runner does not exist.

    Returns:
        The updated runner record.
    """

    runner = db.get(Runner, runner_id)

    if runner is None:
        raise HTTPException(
            status_code=404,
            detail="Runner not found",
        )

    runner.status = "alive"
    runner.last_heartbeat = datetime.now(timezone.utc)

    db.commit()
    db.refresh(runner)

    return runner