"""
Freight runner entrypoint.

Registers the runner with the Freight server, starts the background
heartbeat loop, and keeps the runner process alive.
"""

import time

from runner.config import RUNNER_NAME
from runner.registration import register_runner, start_heartbeat


def main() -> None:
    """
    Start and maintain the Freight runner process.
    """
    print(f"[runner] registering {RUNNER_NAME}...")

    runner_id = register_runner(RUNNER_NAME)

    print(f"[runner] registered with id={runner_id}")

    start_heartbeat(runner_id)

    print("[runner] heartbeat started")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[runner] shutting down")


if __name__ == "__main__":
    main()