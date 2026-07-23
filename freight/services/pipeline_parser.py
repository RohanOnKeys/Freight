"""
Pipeline definition parsing.

Freight pipelines can be provided in two ways:

* As a local file path, used by the CLI (`freight run <path>`) when a
  developer runs a pipeline directly on their own machine.
* As raw YAML text already fetched from GitHub at a specific commit,
  used by the webhook ingestion path so pipeline behavior always
  matches the commit that was actually pushed.

Both entry points parse to the same in-memory pipeline dictionary and
are otherwise handled identically by the rest of the pipeline service.
"""

from pathlib import Path

import yaml


def parse_pipeline(file_path: str | Path) -> dict:
    """
    Load and parse a `.freight.yml` pipeline file from local disk.

    Used by the local CLI, where the pipeline file is a real path on
    the machine running `freight run`.

    Args:
        file_path:
            Path to the pipeline definition file.

    Returns:
        The parsed pipeline definition.

    Raises:
        FileNotFoundError:
            If no file exists at `file_path`.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"{file_path} does not exist."
        )

    with open(path, "r", encoding="utf-8") as f:
        pipeline = yaml.safe_load(f)

    return pipeline


def parse_pipeline_text(content: str) -> dict:
    """
    Parse a `.freight.yml` pipeline definition already held in memory.

    Used by the GitHub webhook ingestion path, where the file's
    contents were already fetched from GitHub's API at the exact
    pushed commit and never touch the Freight server's local
    filesystem.

    Args:
        content:
            Raw YAML text of the pipeline definition.

    Returns:
        The parsed pipeline definition.

    Raises:
        yaml.YAMLError:
            If `content` is not valid YAML.
    """

    return yaml.safe_load(content)