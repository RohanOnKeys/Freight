"""
Docker-based job execution for the Freight runner.

Creates an isolated per-job workspace and executes the job's configured
script inside a Docker container.
"""

from pathlib import Path

import docker


def run_job(job_id: int, image: str, script: list[str]) -> tuple[int, str]:
    """
    Execute a Freight job inside a Docker container.

    Args:
        job_id: Unique identifier of the Freight job.
        image: Docker image used to execute the job.
        script: Commands to execute sequentially inside the container.

    Returns:
        A tuple containing the container exit code and captured output.
    """
    client = docker.from_env()

    workspace = Path("workspace") / str(job_id)
    workspace.mkdir(parents=True, exist_ok=True)

    command = " && ".join(script)

    container = client.containers.run(
        image=image,
        command=["sh", "-c", command],
        volumes={
            str(workspace.resolve()): {
                "bind": "/workspace",
                "mode": "rw",
            }
        },
        working_dir="/workspace",
        detach=True,
    )

    try:
        result = container.wait()
        exit_code = result["StatusCode"]
        output = container.logs().decode("utf-8", errors="replace")
    finally:
        container.remove()

    return exit_code, output