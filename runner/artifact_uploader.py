"""
Artifact upload support for the Freight runner.

Discovers files declared in a job's artifact configuration and uploads
them to the Freight server after successful execution.
"""

from glob import glob
from pathlib import Path

import requests

from runner.config import SERVER_URL


def upload_artifacts(
    job_id: int,
    workspace: Path,
    artifacts_config: dict,
) -> None:
    """
    Upload all configured artifacts for a completed job.

    Args:
        job_id:
            Identifier of the completed Freight job.

        workspace:
            Workspace directory used during job execution.

        artifacts_config:
            Artifact configuration returned by the Freight server.
            Expected format::

                {
                    "paths": [
                        "dist/*",
                        "reports/**/*.xml",
                    ]
                }

    Raises:
        requests.HTTPError:
            If the Freight server rejects an uploaded artifact.
    """

    patterns = artifacts_config.get("paths", [])

    if not patterns:
        print("[runner] no artifacts configured")
        return

    uploaded = 0

    for pattern in patterns:
        matches = glob(
            str(workspace / pattern),
            recursive=True,
        )

        for match in matches:
            artifact = Path(match)

            if not artifact.is_file():
                continue

            relative_path = artifact.relative_to(workspace)

            with artifact.open("rb") as file:
                response = requests.post(
                    f"{SERVER_URL}/jobs/{job_id}/artifacts",
                    data={
                        "path": str(relative_path),
                    },
                    files={
                        "file": file,
                    },
                    timeout=30,
                )

            response.raise_for_status()

            uploaded += 1

            print(
                f"[runner] uploaded artifact: "
                f"{relative_path}"
            )

    print(
        f"[runner] uploaded "
        f"{uploaded} artifact(s)"
    )