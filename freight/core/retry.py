"""
Job retry and backoff logic for Freight.

When a job fails, Freight decides whether to retry it by comparing the
number of attempts already made (`Job.retries`) against the job's
configured retry budget (`Job.max_retries`, parsed from the pipeline's
`retries:` field).

Retries are never requeued immediately. Requeuing a failing job at full
speed risks hammering a broken build step or a flaky dependency in a
tight loop, so each retry waits out an exponentially increasing backoff
before it becomes eligible to run again. That delay is enforced through
a Redis-backed delayed queue (`freight.services.queue`) rather than
blocking the request thread, since `handle_job_failure` runs
synchronously inside the `/jobs/{id}/complete` HTTP handler.

A background task (`monitor_retries`) periodically promotes jobs whose
backoff window has elapsed back onto the live work queue, the same way
`freight.core.heartbeat_monitor` periodically checks for dead runners.
Both are started as asyncio background tasks in `freight.main`'s
application lifespan.
"""

import asyncio
import traceback

from sqlalchemy.orm import Session

from freight.models.job import Job
from freight.services.queue import promote_ready_retries, schedule_retry

BASE_BACKOFF_SECONDS = 2
"""Base used for exponential backoff: delay = BASE_BACKOFF_SECONDS ** attempt."""

MAX_BACKOFF_SECONDS = 60
"""Upper bound on retry delay, regardless of attempt count."""

RETRY_CHECK_INTERVAL = 5
"""How often, in seconds, the background task looks for retries whose
backoff window has elapsed."""


def compute_backoff_seconds(attempt: int) -> float:
    """
    Compute the exponential backoff delay for a given retry attempt.

    Args:
        attempt:
            The 1-indexed attempt number this delay is being computed
            for (1 for the first retry, 2 for the second, and so on).
            Callers pass `job.retries` *after* incrementing it, so the
            first retry backs off by `BASE_BACKOFF_SECONDS ** 1`.

    Returns:
        Delay in seconds before the job becomes eligible to run again,
        capped at `MAX_BACKOFF_SECONDS`.
    """

    delay = BASE_BACKOFF_SECONDS**attempt

    return min(delay, MAX_BACKOFF_SECONDS)


def handle_job_failure(db: Session, job: Job) -> bool:
    """
    Decide whether a failed job should be retried, and requeue it if so.

    Compares attempts already made (`job.retries`) against the job's
    configured limit (`job.max_retries`). If attempts remain, the job is
    reset to `queued` (clearing its runner assignment and timestamps,
    the same fields `freight.core.heartbeat_monitor` clears when
    recovering a dead runner's job) and scheduled to reappear on the
    work queue after an exponential backoff delay. Downstream jobs stay
    blocked while a retry is pending, since the job hasn't reached a
    terminal state.

    If no attempts remain, this function makes no changes and leaves
    the caller (`freight.services.scheduler.on_job_complete`)
    responsible for finalizing the job as permanently `failed`.

    Args:
        db:
            Active database session. This function commits the job's
            requeue itself; the caller does not need to commit again
            for the fields this function touches.

        job:
            The job that just reported a failed execution. Expected to
            already be attached to `db`.

    Returns:
        True if the job was requeued for another attempt (the caller
        should treat the job as not-yet-terminal and stop). False if
        the retry budget is exhausted and the caller should finalize
        the job as failed.
    """

    print(
        f"[retry] entered "
        f"retries={job.retries} "
        f"max={job.max_retries}"
    )

    if job.retries >= job.max_retries:
        print(
            f"[retry] job={job.id} exhausted retries "
            f"({job.retries}/{job.max_retries})"
        )
        return False

    job.retries += 1
    job.status = "queued"
    job.runner_id = None
    job.started_at = None
    job.finished_at = None

    db.commit()

    delay = compute_backoff_seconds(job.retries)

    schedule_retry(job.id, delay)

    print(
        f"[retry] job={job.id} failed; "
        f"attempt {job.retries}/{job.max_retries} "
        f"will requeue in {delay:.0f}s"
    )

    return True


async def monitor_retries() -> None:
    """
    Continuously promote jobs whose retry backoff has elapsed.

    Runs for the lifetime of the Freight server. Every
    `RETRY_CHECK_INTERVAL` seconds, checks the Redis-backed retry queue
    for jobs whose backoff window has elapsed and pushes them back onto
    the live work queue for a runner to claim.
    """

    print("[retry] monitor started")

    while True:

        try:
            promoted = promote_ready_retries()

            for job_id in promoted:
                print(
                    f"[retry] promoted job={job_id}"
                )

        except Exception as exc:
            print(f"[retry] ERROR: {exc}")
            traceback.print_exc()

        await asyncio.sleep(RETRY_CHECK_INTERVAL)