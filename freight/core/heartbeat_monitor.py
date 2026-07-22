import asyncio
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from freight.db.session import SessionLocal
from freight.models.job import Job
from freight.models.runner import Runner
from freight.services.queue import push_job

HEARTBEAT_TIMEOUT = timedelta(seconds=30)
CHECK_INTERVAL = 15


async def monitor_runners() -> None:
    """Continuously monitors runner heartbeats and recovers abandoned jobs.

    This background task periodically inspects all runners marked as
    ``alive``. If a runner has not sent a heartbeat within the configured
    timeout window, it is considered dead.

    For every timed-out runner, the monitor:

    1. Marks the runner as ``dead``.
    2. Finds all jobs currently assigned to that runner.
    3. Resets those jobs back to the ``queued`` state.
    4. Removes the runner assignment.
    5. Pushes the jobs back into the Redis queue for another runner.

    The monitor runs indefinitely until the application shuts down.

    Returns:
        None
    """
    while True:
        db: Session = SessionLocal()

        try:
            _check_runner_health(db)
        finally:
            db.close()

        await asyncio.sleep(CHECK_INTERVAL)


def _check_runner_health(db: Session) -> None:
    """Checks all active runners for heartbeat timeouts.

    Args:
        db: Active SQLAlchemy database session.

    Returns:
        None
    """
    runners = (
        db.query(Runner)
        .filter(Runner.status == "alive")
        .all()
    )

    now = datetime.utcnow()

    for runner in runners:
        if now - runner.last_heartbeat > HEARTBEAT_TIMEOUT:
            _recover_runner(db, runner)


def _recover_runner(db: Session, runner: Runner) -> None:
    """Recovers jobs belonging to a timed-out runner.

    Args:
        db: Active SQLAlchemy database session.
        runner: Runner that has exceeded the heartbeat timeout.

    Returns:
        None
    """
    runner.status = "dead"

    jobs = (
        db.query(Job)
        .filter(
            Job.runner_id == runner.id,
            Job.status == "running",
        )
        .all()
    )

    for job in jobs:
        job.status = "queued"
        job.runner_id = None

    db.commit()

    for job in jobs:
        push_job(job.id)