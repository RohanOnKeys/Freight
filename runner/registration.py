"""
Runner registration and heartbeat management.

Handles runner registration with the Freight server and periodically
sends heartbeat requests to indicate that the runner is alive.
"""

import threading
import time

import httpx

from runner.config import HEARTBEAT_INTERVAL, SERVER_URL


def register_runner(hostname: str) -> int:
    """
    Register a runner with the Freight server.

    Args:
        hostname: Name used to identify the runner.

    Returns:
        The unique runner ID assigned by the server.
    """
    response = httpx.post(
        f"{SERVER_URL}/runners/register",
        json={"hostname": hostname},
        timeout=10.0,
    )
    response.raise_for_status()

    return response.json()["id"]


def heartbeat_loop(runner_id: int) -> None:
    """
    Continuously send heartbeat requests to the Freight server.

    Args:
        runner_id: Unique ID of the registered runner.
    """
    while True:
        try:
            response = httpx.post(
                f"{SERVER_URL}/runners/{runner_id}/heartbeat",
                timeout=10.0,
            )
            response.raise_for_status()

        except httpx.HTTPError as exc:
            print(f"[runner] heartbeat failed: {exc}")

        time.sleep(HEARTBEAT_INTERVAL)


def start_heartbeat(runner_id: int) -> threading.Thread:
    """
    Start the heartbeat loop in a background daemon thread.

    Args:
        runner_id: Unique ID of the registered runner.

    Returns:
        The background heartbeat thread.
    """
    thread = threading.Thread(
        target=heartbeat_loop,
        args=(runner_id,),
        daemon=True,
    )
    thread.start()

    return thread