from pathlib import Path

import yaml


def parse_pipeline(file_path: str | Path) -> dict:
    """
    Load and parse a .freight.yml pipeline file.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(
            f"{file_path} does not exist."
        )

    with open(path, "r", encoding="utf-8") as f:
        pipeline = yaml.safe_load(f)

    return pipeline