from __future__ import annotations

import sys

from .auto import PoytoClient
from .cli_dispatch import dump, execute
from .cli_parser import build_parser
from .exceptions import PoytoError


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        with PoytoClient(
            token=args.global_token,
            token_file=args.global_token_file,
            refresh_token=args.global_refresh_token,
        ) as client:
            dump(execute(parser, args, client))
    except PoytoError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
