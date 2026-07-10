import redis

from freight.core.config import settings


redis_client = redis.Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)


def push_job(job_id: int) -> None:
    redis_client.lpush(
        "freight:queue",
        str(job_id),
    )


def claim_job():
    return redis_client.brpoplpush(
        "freight:queue",
        "freight:processing",
        timeout=0,
    )