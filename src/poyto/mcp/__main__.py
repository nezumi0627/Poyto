from __future__ import annotations

from .config import build_parser
from .server import build_server


def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    server = build_server(
        host=args.host,
        port=args.port,
        read_only=args.read_only,
    )
    server.run(transport=args.transport)


if __name__ == "__main__":
    main()
