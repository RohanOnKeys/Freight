"""
Freight runner entrypoint.

Registers the runner with the Freight server, starts the background
heartbeat loop, waits for queued jobs, confirms ownership with the
Freight server, resolves execution secrets, checks out the job's
source commit, executes jobs, uploads produced artifacts, and reports
the final execution result.
"""

from pathlib import Path
from typing import Any

import requests

from runner.artifact_uploader import upload_artifacts
from runner.claim import acknowledge_job, wait_for_job
from runner.config import GITHUB_TOKEN, RUNNER_NAME, SERVER_URL
from runner.executor import run_job
from runner.registration import register_runner, start_heartbeat
from runner.secret_injector import (
    build_environment,
    fetch_job_secrets,
)
from runner.source_checkout import checkout_source


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
        Complete job payload returned by the Freight server, including
        the source repository, branch, and commit to check out before
        execution when the job originated from a GitHub webhook.

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

    Args:
        job_id:
            Identifier of the completed Freight job.

        exit_code:
            Container exit code.

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

    Runner lifecycle:

    1. Register with the Freight server.
    2. Start heartbeat reporting.
    3. Wait for queued jobs.
    4. Confirm ownership.
    5. Fetch job configuration.
    6. Resolve execution secrets.
    7. Check out the job's source commit, if any.
    8. Execute the Docker container.
    9. Upload produced artifacts.
    10. Report completion.
    11. Acknowledge the Redis queue.
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

            if job_id is None:
                continue

            print(f"[runner] received job={job_id}")

            if not confirm_job_claim(job_id, runner_id):
                print(
                    f"[runner] ownership denied for job={job_id}; "
                    "job will not be executed"
                )
                continue

            job = fetch_job(job_id)

            secrets = fetch_job_secrets(job_id)

            environment = build_environment(
                job_environment=job.get("environment", {}),
                secrets=secrets,
            )

            workspace = Path("workspace") / str(job_id)
            workspace.mkdir(parents=True, exist_ok=True)

            repo = job.get("repo")
            commit_sha = job.get("commit_sha")

            if repo and commit_sha:
                print(
                    f"[runner] checking out {repo}@{commit_sha} "
                    f"for job={job_id}"
                )
                checkout_source(
                    workspace=workspace,
                    repo=repo,
                    commit_sha=commit_sha,
                    github_token=GITHUB_TOKEN,
                )
            else:
                print(
                    f"[runner] job={job_id} has no source repo; "
                    "running script in an empty workspace"
                )

            print(
                f"[runner] executing job={job_id} "
                f"image={job['image']}"
            )

            exit_code, _, workspace = run_job(
                job_id=job_id,
                image=job["image"],
                script=job["script"],
                workspace=workspace,
                environment=environment,
            )

            if exit_code == 0:
                try:
                    upload_artifacts(
                        job_id=job_id,
                        workspace=workspace,
                        artifacts_config=job.get(
                            "artifacts_config",
                            {},
                        ),
                    )
                except requests.HTTPError as exc:
                    print(
                        f"[runner] artifact upload failed: {exc}"
                    )

            report_job_completion(
                job_id=job_id,
                exit_code=exit_code,
            )

            acknowledge_job(
                runner_id=runner_id,
                job_id=job_id,
            )

            print(
                f"[runner] reported completion for job={job_id}"
            )

    except KeyboardInterrupt:
        print("\n[runner] shutting down")


if __name__ == "__main__":
    main()