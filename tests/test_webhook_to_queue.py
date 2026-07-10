import json

from fastapi.testclient import TestClient

from freight.main import app

client = TestClient(app)


def test_webhook_creates_pipeline():
    with open(
        "tests/fixtures/github_push_payload.json",
        "r",
        encoding="utf-8",
    ) as f:
        payload = json.load(f)

    response = client.post(
        "/webhook/",
        json=payload,
    )

    assert response.status_code == 201