import argparse

from cli.commands.run import run_command


def parse_args():
    """
    Build and parse CLI arguments.
    """

    parser = argparse.ArgumentParser(
        prog="freight",
        description="Freight CI/CD CLI",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
    )

    # freight run <pipeline>
    run_parser = subparsers.add_parser(
        "run",
        help="Run a local Freight pipeline",
    )

    run_parser.add_argument(
        "pipeline",
        help="Path to the .freight.yml file",
    )

    run_parser.set_defaults(func=run_command)

    return parser.parse_args()