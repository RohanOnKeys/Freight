"""
GitHub webhook schemas.

These models represent the subset of the GitHub webhook payload used by
Freight during pipeline ingestion.
"""

from pydantic import BaseModel


class Repository(BaseModel):
    """
    Repository information contained within a GitHub webhook payload.
    """

    name: str


class GitHubWebhook(BaseModel):
    """
    Minimal GitHub push event payload required by Freight.
    """

    ref: str
    after: str
    repository: Repository