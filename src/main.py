from __future__ import annotations

import argparse

import uvicorn

from . import database
from .api_client import build_provider
from .configuration import load_settings
from .scheduler import SweepstakeService
from .sharepoint import SharePointClient
from .site import build_static_site
from .teams import build_notifier


def main() -> None:
    parser = argparse.ArgumentParser(description="World Cup sweepstake automation")
    parser.add_argument("--output-dir", help="Override site output directory for build-site")
    parser.add_argument("--base-path", default="", help="Base path prefix for generated site links")
    parser.add_argument(
        "command",
        choices=["init-db", "sync-participants", "run-once", "serve", "build-site"],
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

    if args.command == "serve":
        uvicorn.run("src.web:app", host="0.0.0.0", port=8000, reload=False)
        return

    if args.command == "build-site":
        build_static_site(
            settings,
            output_dir=(settings.root_dir / args.output_dir) if args.output_dir else None,
            site_base_path=args.base_path,
        )
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
