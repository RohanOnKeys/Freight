"""
Freight runner entrypoint.

Registers the runner with the Freight server, starts the background
heartbeat loop, waits for queued jobs, and confirms job ownership with
the Freight server before execution.
"""

import requests

from runner.claim import wait_for_job
from runner.config import RUNNER_NAME, SERVER_URL
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
                print(
                    f"[runner] successfully claimed job={job_id}"
                )

                # Docker execution is implemented in Week 2, Day 3.
            else:
                print(
                    f"[runner] ownership denied for job={job_id}; "
                    "job will not be executed"
                )

    except KeyboardInterrupt:
        print("\n[runner] shutting down")


if __name__ == "__main__":
    main()