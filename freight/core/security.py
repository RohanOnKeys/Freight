import hashlib
import hmac

from freight.core.config import settings


def verify_github_signature(
    payload: bytes,
    signature: str | None,
) -> bool:
    if not signature:
        return False

    expected = "sha256=" + hmac.new(
        settings.GITHUB_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(expected, signature)