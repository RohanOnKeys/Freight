"""
GitHub API client for fetching pipeline definitions.

When a GitHub webhook triggers a pipeline, Freight needs the exact
`.freight.yml` that existed in the pushed repository at the pushed
commit, not whatever file happens to sit on the Freight server's own
disk. This module fetches that file directly from GitHub's REST
Contents API using the repository and commit information contained in
the webhook payload.
"""

import base64

import requests

from freight.core.config import settings

GITHUB_API_URL = "https://api.github.com"

class PipelineFileNotFoundError(Exception):
    """Raised when the repository has no pipeline file at the given commit."""


class GitHubFetchError(Exception):
    """Raised when the GitHub API request fails for any other reason."""


def fetch_pipeline_file(
    repo_full_name: str,
    commit_sha: str,
    path: str = ".freight.yml",
) -> str:
    """
    Fetch the raw contents of a pipeline definition file from GitHub.

    Uses GitHub's Contents API to retrieve `path` exactly as it existed
    in `repo_full_name` at `commit_sha`, so pipeline behavior always
    matches the commit that was actually pushed rather than whatever
    file happens to exist on the Freight server.

    Args:
        repo_full_name:
            Repository in `"owner/name"` form, as reported by GitHub's
            webhook payload (`repository.full_name`).

        commit_sha:
            The commit to read the file from (the webhook's `after`
            field for push events).

        path:
            Path to the pipeline file within the repository. Defaults
            to `.freight.yml`.

    Returns:
        The decoded text contents of the file at that commit.

    Raises:
        PipelineFileNotFoundError:
            If no file exists at `path` for that commit (HTTP 404).

        GitHubFetchError:
            If the GitHub API request fails for any other reason, for
            example an invalid token, a private repository without
            access, or a network failure.
    """

    url = f"{GITHUB_API_URL}/repos/{repo_full_name}/contents/{path}"

    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if settings.GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {settings.GITHUB_TOKEN}"

    try:
        response = requests.get(
            url,
            headers=headers,
            params={"ref": commit_sha},
            timeout=10,
        )
    except requests.RequestException as exc:
        raise GitHubFetchError(
            f"Failed to reach GitHub API for "
            f"{repo_full_name}@{commit_sha}: {exc}"
        ) from exc

    if response.status_code == 404:
        raise PipelineFileNotFoundError(
            f"No '{path}' found in {repo_full_name} at commit {commit_sha}"
        )

    if response.status_code != 200:
        raise GitHubFetchError(
            f"GitHub API returned {response.status_code} for "
            f"{repo_full_name}@{commit_sha}: {response.text}"
        )

    payload = response.json()

    if payload.get("encoding") != "base64":
        raise GitHubFetchError(
            f"Unexpected encoding '{payload.get('encoding')}' returned "
            f"for {repo_full_name}/{path}"
        )

    raw_bytes = base64.b64decode(payload["content"])

    return raw_bytes.decode("utf-8")