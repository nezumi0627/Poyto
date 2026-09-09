from __future__ import annotations

import json

from .config import build_parser, settings_from_args
from .server import build_server


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    settings = settings_from_args(args)

    if args.print_config:
        print(json.dumps(settings.as_public_dict(), indent=2, sort_keys=True))
        return

    server = build_server(
        host=settings.host,
        port=settings.port,
        read_only=settings.read_only,
    )
    server.run(transport=settings.transport)


if __name__ == "__main__":
    main()
