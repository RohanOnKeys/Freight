import os


SERVER_URL = os.getenv(
    "SERVER_URL",
    "http://127.0.0.1:8000",
)

RUNNER_NAME = os.getenv(
    "RUNNER_NAME",
    "freight-runner",
)

HEARTBEAT_INTERVAL = int(
    os.getenv("HEARTBEAT_INTERVAL", "10")
)