"""
Source checkout utilities for the Freight runner.

Before a job's script executes inside its Docker container, the runner
must ensure the actual pushed repository content is present in the
job's workspace. This module fetches exactly the commit associated
with the job's pipeline (as recorded by the GitHub webhook) using a
shallow, single-commit fetch, and checks it out into the workspace
directory that gets mounted into the execution container.

Jobs that were not triggered by a GitHub push (for example, pipelines
submitted through the local CLI) have no `repo`/`commit_sha` and are
left untouched; the workspace remains whatever the job's own script
produces, matching Freight's existing local-execution behavior.
"""

import subprocess
from pathlib import Path


def _run_git(args: list[str], cwd: Path) -> None:
    """
    Run a git command inside `cwd`, raising with full context on failure.

    Args:
        args:
            Git subcommand and arguments, excluding the leading `git`.

        cwd:
            Directory the command should run in.

    Raises:
        RuntimeError:
            If the git command exits with a non-zero status. The error
            message includes the command that failed and git's stderr
            output.
    """

    result = subprocess.run(
        ["git", *args],
        cwd=cwd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} failed in {cwd}: {result.stderr.strip()}"
        )


def build_remote_url(repo: str, github_token: str | None = None) -> str:
    """
    Build the HTTPS clone URL for a GitHub repository.

    Args:
        repo:
            Repository full name, e.g. `"owner/name"`.

        github_token:
            Optional GitHub personal access token or installation
            token. Required for private repositories; ignored for
            public ones.

    Returns:
        An `https://` clone URL, with the token embedded as HTTP basic
        auth when provided.
    """

    if github_token:
        return f"https://x-access-token:{github_token}@github.com/{repo}.git"

    return f"https://github.com/{repo}.git"


def checkout_source(
    workspace: Path,
    repo: str | None,
    commit_sha: str | None,
    github_token: str | None = None,
) -> None:
    """
    Fetch and check out a single commit into a job's workspace.

    Performs a shallow, single-commit fetch (`git fetch --depth 1
    origin <sha>`) rather than a full clone, since only the exact
    commit the webhook recorded is needed to execute the job's script.

    If `repo` or `commit_sha` is missing (for example, a pipeline
    submitted through the local CLI rather than a GitHub push), this
    function does nothing and the workspace is left as-is.

    Args:
        workspace:
            Directory to check the source out into. Must already
            exist and be empty; this is the same directory that gets
            mounted into the job's execution container.

        repo:
            Repository full name, e.g. `"owner/name"`.

        commit_sha:
            The exact commit to check out.

        github_token:
            Optional token used to authenticate against private
            repositories.

    Raises:
        RuntimeError:
            If any underlying git command fails, for example because
            the commit is unreachable, or the repository does not
            exist, or the repository is private without a valid
            token.
    """

    if not repo or not commit_sha:
        return

    remote_url = build_remote_url(repo, github_token)

    _run_git(["init"], cwd=workspace)
    _run_git(["remote", "add", "origin", remote_url], cwd=workspace)
    _run_git(
        ["fetch", "--depth", "1", "origin", commit_sha],
        cwd=workspace,
    )
    _run_git(["checkout", "FETCH_HEAD"], cwd=workspace)