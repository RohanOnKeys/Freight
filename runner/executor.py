"""
Docker-based job execution for the Freight runner.

Creates an isolated per-job workspace, executes the job's configured
script inside a Docker container, and streams container output to the
Freight server while execution is in progress.
"""

from pathlib import Path

import docker

from runner.log_streamer import stream_logs


def run_job(
    job_id: int,
    image: str,
    script: list[str],
) -> tuple[int, str, Path]:
    """
    Execute a Freight job inside a Docker container.

    A dedicated workspace is created for every job. Standard output and
    standard error are streamed to the Freight server while also being
    captured locally.

    Args:
        job_id:
            Identifier of the Freight job.

        image:
            Docker image used to execute the job.

        script:
            Commands executed sequentially inside the container.

    Returns:
        A tuple containing:

        - Container exit code.
        - Complete captured output.
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