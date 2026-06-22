from __future__ import annotations

import argparse

from . import database
from .api_client import build_provider
from .configuration import load_settings
from .scheduler import SweepstakeService
from .sharepoint import SharePointClient
from .teams import build_notifier


def main() -> None:
    parser = argparse.ArgumentParser(description="World Cup sweepstake automation")
    parser.add_argument(
        "command",
        choices=["init-db", "sync-participants", "run-once"],
        help="Operation to execute",
    )
    args = parser.parse_args()

    settings = load_settings()
    connection = database.connect(settings.database_path)

    if args.command == "init-db":
        database.migrate(connection)
        return

    if args.command == "sync-participants":
        database.migrate(connection)
        database.import_participants(connection, settings.participants_csv)
        return

    service = SweepstakeService(
        settings=settings,
        provider=build_provider(settings),
        notifier=build_notifier(settings),
        sharepoint_client=SharePointClient(settings),
    )
    service.run_once()


if __name__ == "__main__":
    main()

