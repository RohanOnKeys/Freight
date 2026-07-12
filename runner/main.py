"""
Freight runner entrypoint.

Registers the runner with the Freight server, starts the background
heartbeat loop, waits for queued jobs, and confirms job ownership with
the Freight server before execution.
"""

from typing import Any

import requests

from runner.claim import acknowledge_job, wait_for_job
from runner.config import RUNNER_NAME, SERVER_URL
from runner.executor import run_job
from runner.registration import register_runner, start_heartbeat


def confirm_job_claim(job_id: int, runner_id: int) -> bool:
    """
    Confirm ownership of a Redis-claimed job with the Freight server.

    Returns True only when the server successfully assigns the job to
    this runner. A rejected claim must never proceed to execution.
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
    Fetch the execution configuration for a claimed job.

    Args:
        job_id: Identifier of the job to retrieve.

    Returns:
        The complete job payload returned by the Freight server.

    Raises:
        requests.HTTPError: If the server cannot return the requested job.
    """

    response = requests.get(
        f"{SERVER_URL}/jobs/{job_id}",
        timeout=10,
    )

    response.raise_for_status()

    return response.json()


def report_job_completion(job_id: int, exit_code: int) -> None:
    """
    Report a finished job's execution result to the Freight server.

    A zero exit code marks the job as completed. Any non-zero exit code
    marks it as failed. Successful completion allows the server-side
    scheduler to release newly unblocked downstream jobs.

    Args:
        job_id: Identifier of the completed job.
        exit_code: Exit code returned by the job container.

    Raises:
        requests.HTTPError: If the Freight server rejects the result.
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
    Start and maintain the Freight runner process.

    After registration, the runner continuously waits for jobs using an
    atomic Redis operation and confirms database ownership before any
    future execution step is allowed to proceed.
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

            if confirm_job_claim(job_id, runner_id):
                print(f"[runner] successfully claimed job={job_id}")

                job = fetch_job(job_id)

                print(
                    f"[runner] executing job={job_id} "
                    f"image={job['image']}"
                )

                exit_code, _ = run_job(
                    job_id=job_id,
                    image=job["image"],
                    script=job["script"],
                )

                print(
                    f"[runner] job={job_id} finished "
                    f"with exit_code={exit_code}"
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
            else:
                print(
                    f"[runner] ownership denied for job={job_id}; "
                    "job will not be executed"
                )

    except KeyboardInterrupt:
        print("\n[runner] shutting down")


if __name__ == "__main__":
    main()