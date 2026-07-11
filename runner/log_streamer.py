"""
Job log streaming utilities for the Freight runner.

This module forwards container output from a runner to the Freight server
while a job is executing.

Docker log output is consumed line-by-line and each line is sent to the
job log ingestion endpoint. The server is responsible for appending the
received chunks to the persistent ``logs/{job_id}.log`` file.
"""

from collections.abc import Iterable

import requests

from runner.config import SERVER_URL


def send_log_chunk(job_id: int, chunk: str) -> None:
    """
    Send a single log chunk to the Freight server.

    Args:
        job_id: Identifier of the job producing the output.
        chunk: Plain-text output to append to the job's log file.

    Raises:
        requests.HTTPError: If the server rejects the log chunk.
    """

    response = requests.post(
        f"{SERVER_URL}/jobs/{job_id}/logs",
        data=chunk,
        headers={
            "Content-Type": "text/plain",
        },
        timeout=10,
    )

    response.raise_for_status()


def stream_logs(
    job_id: int,
    log_stream: Iterable[bytes],
) -> str:
    """
    Forward Docker output to the Freight server line-by-line.

    Each item yielded by the Docker log stream is decoded as UTF-8,
    forwarded to the server, and accumulated locally so the executor can
    still return the complete captured output after execution.

    Args:
        job_id: Identifier of the running job.
        log_stream: Iterable yielding raw Docker log output as bytes.

    Returns:
        The complete decoded output produced by the container.
    """

    captured_output: list[str] = []

    for raw_line in log_stream:
        line = raw_line.decode(
            "utf-8",
            errors="replace",
        )

        if not line.endswith("\n"):
            line += "\n"

        send_log_chunk(
            job_id=job_id,
            chunk=line,
        )

        captured_output.append(line)

    return "".join(captured_output)