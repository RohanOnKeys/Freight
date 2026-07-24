"""
Redis-backed job queueing for Freight.

Two Redis structures are used:

* `freight:queue` — a list of job IDs ready for a runner to claim right
  now. Runners pop from this atomically via `BRPOPLPUSH` (see
  `runner.claim.wait_for_job`).
* `freight:retry` — a sorted set of job IDs waiting out an exponential
  backoff after a failed attempt (see `freight.core.retry`), scored by
  the Unix timestamp at which each becomes eligible to run again. A
  background task periodically promotes eligible entries back onto
  `freight:queue`.
"""

import time

import redis

from freight.core.config import settings

redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)

QUEUE_KEY = "freight:queue"
PROCESSING_KEY = "freight:processing"
RETRY_KEY = "freight:retry"


def push_job(job_id: int) -> None:
    """
    Push a job onto the live work queue for runners to claim.

    Args:
        job_id:
            Identifier of the job now ready for execution.
    """

    redis_client.lpush(
        QUEUE_KEY,
        str(job_id),
    )


def claim_job():
    """
    Atomically claim the next available job from the live work queue.

    Moves the job ID from `freight:queue` to `freight:processing` so a
    crash between claiming and recording ownership doesn't silently
    drop the job. Runners use the per-runner variant in
    `runner.claim.wait_for_job` instead; this generic version exists
    for local tooling and tests.

    Returns:
        The claimed job ID as a string, or `None` if no job is
        available.
    """

    return redis_client.brpoplpush(
        QUEUE_KEY,
        PROCESSING_KEY,
        timeout=0,
    )


def schedule_retry(job_id: int, delay_seconds: float) -> None:
    """
    Schedule a failed job to reappear on the work queue after a delay.

    The job is recorded in a Redis sorted set rather than pushed
    directly, so it doesn't become claimable again until its backoff
    window has elapsed. `freight.core.retry.monitor_retries`
    periodically promotes eligible entries back onto the live queue.

    Args:
        job_id:
            Identifier of the job to retry.

        delay_seconds:
            Number of seconds to wait before the job becomes eligible
            to run again.
    """

    eligible_at = time.time() + delay_seconds

    redis_client.zadd(
        RETRY_KEY,
        {str(job_id): eligible_at},
    )


def promote_ready_retries() -> list[int]:
    """
    Move every retry-eligible job back onto the live work queue.

    Returns:
        List of job IDs that were promoted during this call.
    """

    now = time.time()

    ready = redis_client.zrangebyscore(
        RETRY_KEY,
        min="-inf",
        max=now,
    )

    promoted: list[int] = []

    for job_id_str in ready:

        # ZREM reports how many members it actually removed. Guarding
        # on that return value keeps this idempotent if this function
        # is ever called concurrently (for example, a future second
        # Freight server instance polling the same Redis).
        removed = redis_client.zrem(
            RETRY_KEY,
            job_id_str,
        )

        if not removed:
            continue

        job_id = int(job_id_str)

        push_job(job_id)

        promoted.append(job_id)

    return promoted