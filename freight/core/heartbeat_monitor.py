"""
Heartbeat monitoring for Freight runners.

Monitors registered runners for heartbeat timeouts. Timed-out runners
are marked as dead and any running jobs assigned to them are requeued.
"""

import asyncio
import traceback
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from freight.db.session import SessionLocal
from freight.models.job import Job
from freight.models.runner import Runner
from freight.services.queue import push_job

HEARTBEAT_TIMEOUT = timedelta(seconds=30)
CHECK_INTERVAL = 15


async def monitor_runners() -> None:
    """Continuously monitor runner heartbeats."""
    print("[heartbeat] monitor started")

    while True:
        db: Session = SessionLocal()

        try:
            _check_runner_health(db)

        except Exception as exc:
            print(f"[heartbeat] ERROR: {exc}")
            traceback.print_exc()

        finally:
            db.close()

        await asyncio.sleep(CHECK_INTERVAL)


def _check_runner_health(db: Session) -> None:
    """Check all alive runners for heartbeat timeouts."""
    print("[heartbeat] checking runners...")

    now = datetime.utcnow()

    runners = (
        db.query(Runner)
        .filter(Runner.status == "alive")
        .all()
    )

    for runner in runners:
        print(
            f"[heartbeat] "
            f"runner={runner.id} "
            f"status={runner.status} "
            f"last={runner.last_heartbeat}"
        )

        if runner.last_heartbeat is None:
            continue

        delta = now - runner.last_heartbeat

        print(f"[heartbeat] age={delta}")

        if delta > HEARTBEAT_TIMEOUT:
            print(
                f"[heartbeat] runner {runner.id} timed out"
            )
            _recover_runner(db, runner)


def _recover_runner(
    db: Session,
    runner: Runner,
) -> None:
    """Recover jobs from a dead runner."""
    print(f"[heartbeat] recovering runner {runner.id}")

    runner.status = "dead"

    jobs = (
        db.query(Job)
        .filter(
            Job.runner_id == runner.id,
            Job.status == "running",
        )
        .all()
    )

    print(f"[heartbeat] found {len(jobs)} running job(s)")

    for job in jobs:
        print(f"[heartbeat] requeueing job {job.id}")

        job.status = "queued"
        job.runner_id = None
        job.started_at = None

    db.commit()

    for job in jobs:
        push_job(job.id)
        print(f"[heartbeat] pushed job {job.id} to Redis")

    print(f"[heartbeat] recovery complete for runner {runner.id}")