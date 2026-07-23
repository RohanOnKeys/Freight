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

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
"""
Optional GitHub token used to check out private repositories.

Not required for public repositories. Set this in the runner's own
environment (it never travels through Freight's API) when jobs need to
check out source from a private repo.
"""