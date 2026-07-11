from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from freight.db.session import get_db
from freight.models.runner import Runner
from freight.schemas.runner import RunnerOut, RunnerRegisterIn

router = APIRouter(prefix="/runners", tags=["runners"])

@router.post("/register", response_model=RunnerOut, status_code=201)
def register_runner(
    payload: RunnerRegisterIn,
    db: Session = Depends(get_db),
):
    runner = Runner(
        hostname=payload.hostname,
        status="alive",
        last_heartbeat=datetime.now(timezone.utc),
    )

    db.add(runner)
    db.commit()
    db.refresh(runner)

    return runner


@router.post("/{runner_id}/heartbeat", response_model=RunnerOut)
def heartbeat(
    runner_id: int,
    db: Session = Depends(get_db),
):
    runner = db.get(Runner, runner_id)

    if runner is None:
        raise HTTPException(status_code=404, detail="Runner not found")

    runner.status = "alive"
    runner.last_heartbeat = datetime.now(timezone.utc)

    db.commit()
    db.refresh(runner)

    return runner