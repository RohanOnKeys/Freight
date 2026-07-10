import hashlib
import hmac
import json

from fastapi.testclient import TestClient

from freight.core.config import settings
from freight.main import app

client = TestClient(app)


def test_webhook_creates_pipeline():
    with open(
        "tests/fixtures/github_push_payload.json",
        "r",
        encoding="utf-8",
    ) as f:
        payload = json.load(f)

    payload_bytes = json.dumps(payload).encode("utf-8")

    signature = (
        "sha256="
        + hmac.new(
            settings.GITHUB_WEBHOOK_SECRET.encode(),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
    )

    response = client.post(
        "/webhook/",
        content=payload_bytes,
        headers={
            "Content-Type": "application/json",
            "X-Hub-Signature-256": signature,
        },
    )

    assert response.status_code == 201