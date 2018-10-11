import logging
import sys
from argparse import ArgumentParser
from os import environ, getenv
from typing import List, Optional

from . import __version__
from .exceptions import OsirisError
from .osiris import Osiris


def main(args: Optional[List[str]] = None) -> int:
    """ Main logic. """

    cli_args = ArgumentParser()
    cli_args.add_argument(
        "-c", "--config-file", default="rules.ini", help="the configuration file"
    )
    cli_args.add_argument(
        "-f", "--full", action="store_true", help="perform a full scan of the inbox"
    )
    cli_args.add_argument(
        "-d", "--debug", action="store_true", help="enable debug logging"
    )
    cli_args.add_argument(
        "-l", "--list-actions", action="store_true", help="list available actions"
    )
    cli_args.add_argument("-q", "--quiet", action="store_true", help="silent mode")
    cli_args.add_argument("-v", "--version", action="version", version=__version__)

    options = cli_args.parse_args(args)

    if options.list_actions:
        from .client import Client

        for action, doc in Client.actions():
            print(action)
            print(" ", doc)
        return 0

    if options.debug or getenv("DEBUG"):
        level = logging.DEBUG
        environ["DEBUG"] = "1"
    elif options.quiet:
        level = logging.WARNING
    else:
        level = logging.INFO
    logging.basicConfig(level=level)

    if not options.config_file:
        print("Error: the following arguments are required: -c/--config-file")
        return 1

    try:
        with Osiris(file=options.config_file, full=options.full) as osiris:
            osiris.judge()
        return 0
    except OsirisError as exc:
        print(exc)
        return 1


if __name__ == "__main__":
    exit(main(sys.argv[1:]))
