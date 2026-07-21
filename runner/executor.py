"""
Docker-based job execution for the Freight runner.

Creates an isolated workspace for every Freight job, executes the
configured pipeline script inside a Docker container, streams container
logs to the Freight server during execution, and returns the execution
result to the runner.

This module is intentionally unaware of Freight-specific concepts such
as job claiming, secrets, artifact uploading, scheduling, or database
state. Its sole responsibility is Docker execution.
"""

from pathlib import Path

import docker

from runner.log_streamer import stream_logs


def run_job(
    job_id: int,
    image: str,
    script: list[str],
    environment: dict[str, str] | None = None,
) -> tuple[int, str, Path]:
    """
    Execute a Freight job inside a Docker container.

    A dedicated workspace is created for every job beneath the local
    workspace directory and mounted into the execution container as
    ``/workspace``.

    Standard output and standard error are streamed to the Freight
    server while also being accumulated locally for the final execution
    result.

    Environment variables supplied by the caller are injected directly
    into the execution container. This typically includes decrypted
    Freight secrets and pipeline-defined environment variables.

    Args:
        job_id:
            Identifier of the Freight job.

        image:
            Docker image used to execute the job.

        script:
            Commands executed sequentially inside the container.

        environment:
            Environment variables injected into the execution container.
            If omitted, the container executes without additional
            environment variables.

    Returns:
        A tuple containing:

        - Container exit code.
        - Complete captured stdout/stderr output.
        - Workspace directory used during execution.
    """

    client = docker.from_env()

    workspace = Path("workspace") / str(job_id)

    workspace.mkdir(
        parents=True,
        exist_ok=True,
    )

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
        environment=environment or {},
        detach=True,
    )

    try:
        output = stream_logs(
            job_id=job_id,
            log_stream=container.logs(
                stream=True,
                follow=True,
            ),
        )

        result = container.wait()

        exit_code = result["StatusCode"]

    finally:
        container.remove()

    return (
        exit_code,
        output,
        workspace,
    )