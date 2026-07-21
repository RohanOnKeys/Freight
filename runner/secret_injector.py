"""
Secret resolution support for the Freight runner.

This module retrieves execution secrets from the Freight server
immediately before container startup.

Secrets exist only in memory during execution. They are never written to
disk, logged, or persisted locally.

The returned environment mapping is passed directly to Docker when
starting the job container.
"""

from typing import Any

import requests

from runner.config import SERVER_URL


def fetch_job_secrets(
    job_id: int,
) -> dict[str, str]:
    """
    Retrieve execution secrets for a Freight job.

    Args:
        job_id:
            Identifier of the job being executed.

    Returns:
        Dictionary mapping environment variable names to decrypted
        secret values.

    Raises:
        requests.HTTPError:
            If the Freight server rejects the request.
    """

    response = requests.get(
        f"{SERVER_URL}/jobs/{job_id}/secrets",
        timeout=10,
    )

    response.raise_for_status()

    payload: dict[str, Any] = response.json()

    return payload.get("secrets", {})


def build_environment(
    job_environment: dict[str, str] | None = None,
    secrets: dict[str, str] | None = None,
) -> dict[str, str]:
    """
    Build the complete container environment.

    Environment variables declared by the pipeline are merged with
    resolved Freight secrets. Secret values take precedence when a
    duplicate key exists.

    Args:
        job_environment:
            Environment variables declared in the pipeline.

        secrets:
            Decrypted secrets returned by the Freight server.

    Returns:
        Dictionary suitable for Docker's ``environment=`` argument.
    """

    environment: dict[str, str] = {}

    if job_environment:
        environment.update(job_environment)

    if secrets:
        environment.update(secrets)

    return environment