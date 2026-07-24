"""
Job claiming utilities for the Freight runner.

Provides atomic Redis job claiming by moving jobs from the shared queue
to a runner-specific processing list.
"""

import redis

from freight.core.config import settings


redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
    socket_timeout=None,
)


def wait_for_job(runner_id: int) -> int | None:
    """
    Wait briefly for and atomically claim the next queued job.

    Redis atomically moves the job from the shared queue to the
    runner-specific processing list, ensuring that no two runners can
    receive the same queued job.

    Args:
        runner_id: Identifier of the runner waiting for work.

    Returns:
        The identifier of the atomically claimed job, or None when no
        job becomes available before the timeout elapses.
    """

    job_id = redis_client.brpoplpush(
        "freight:queue",
        f"freight:processing:{runner_id}",
        timeout=1,
    )

    if job_id is None:
        return None

    return int(job_id)


def acknowledge_job(runner_id: int, job_id: int) -> None:
    """
    Remove a successfully processed job from the runner's processing list.

    Args:
        runner_id: Identifier of the runner that claimed the job.
        job_id: Identifier of the job whose result was successfully reported.
    """

    redis_client.lrem(
        f"freight:processing:{runner_id}",
        1,
        str(job_id),
    )