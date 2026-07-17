"""
Freight runner entrypoint.

Registers the runner with the Freight server, starts the background
heartbeat loop, waits for queued jobs, confirms ownership with the
Freight server, executes jobs, uploads produced artifacts, and reports
the final execution result.
"""

from typing import Any

import requests

from runner.artifact_uploader import upload_artifacts
from runner.claim import acknowledge_job, wait_for_job
from runner.config import RUNNER_NAME, SERVER_URL
from runner.executor import run_job
from runner.registration import register_runner, start_heartbeat


def confirm_job_claim(job_id: int, runner_id: int) -> bool:
    """
    Confirm ownership of a Redis-claimed job with the Freight server.

    Returns True only when the server successfully assigns the job to
    this runner. A rejected claim must never proceed to execution.

    Args:
        job_id:
            Identifier of the claimed job.

        runner_id:
            Identifier of the runner requesting ownership.

    Returns:
        True if ownership is granted, otherwise False.
    """

    response = requests.post(
        f"{SERVER_URL}/jobs/{job_id}/claim",
        json={"runner_id": runner_id},
        timeout=10,
    )

    if response.status_code == 200:
        return True

    print(
        f"[runner] claim rejected for job={job_id} "
        f"status={response.status_code}"
    )

    return False


def fetch_job(job_id: int) -> dict[str, Any]:
    """
    Retrieve the execution configuration for a claimed job.

    Args:
        job_id:
            Identifier of the requested job.

    Returns:
        Complete job payload returned by the Freight server.

    Raises:
        requests.HTTPError:
            If the server rejects the request.
    """

    response = requests.get(
        f"{SERVER_URL}/jobs/{job_id}",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def report_job_completion(job_id: int, exit_code: int) -> None:
    """
    Report a completed job to the Freight server.

    Successful execution is determined by a zero exit code. Any non-zero
    exit code is reported as a failed job.

    Args:
        job_id:
            Identifier of the completed job.

        exit_code:
            Container process exit code.

    Raises:
        requests.HTTPError:
            If the Freight server rejects the completion report.
    """

    status = "completed" if exit_code == 0 else "failed"

    response = requests.post(
        f"{SERVER_URL}/jobs/{job_id}/complete",
        json={
            "status": status,
            "exit_code": exit_code,
        },
        timeout=10,
    )

    response.raise_for_status()


def main() -> None:
    """
    Start the Freight runner.

    The runner continuously performs the following lifecycle:

    1. Register with the Freight server.
    2. Start heartbeat reporting.
    3. Wait for queued jobs.
    4. Confirm ownership.
    5. Execute the job.
    6. Upload configured artifacts.
    7. Report completion.
    8. Acknowledge the Redis queue.
    """

    print(f"[runner] registering {RUNNER_NAME}...")

    runner_id = register_runner(RUNNER_NAME)

    print(f"[runner] registered with id={runner_id}")

    start_heartbeat(runner_id)

    print("[runner] heartbeat started")
    print("[runner] waiting for jobs...")

    try:
        while True:
            job_id = wait_for_job(runner_id)

            print(f"[runner] received job={job_id}")

            if not confirm_job_claim(job_id, runner_id):
                print(
                    f"[runner] ownership denied for job={job_id}; "
                    "job will not be executed"
                )
                continue

            print(f"[runner] successfully claimed job={job_id}")

            job = fetch_job(job_id)

            print(
                f"[runner] executing job={job_id} "
                f"image={job['image']}"
            )

            exit_code, _, workspace = run_job(
                job_id=job_id,
                image=job["image"],
                script=job["script"],
            )

            print(
                f"[runner] job={job_id} finished "
                f"with exit_code={exit_code}"
            )

            upload_artifacts(
                job_id=job_id,
                workspace=workspace,
                artifacts_config=job.get(
                    "artifacts_config",
                    {},
                ),
            )

            report_job_completion(
                job_id=job_id,
                exit_code=exit_code,
            )

            acknowledge_job(
                runner_id=runner_id,
                job_id=job_id,
            )

            print(f"[runner] reported completion for job={job_id}")

    except KeyboardInterrupt:
        print("\n[runner] shutting down")


if __name__ == "__main__":
    main()