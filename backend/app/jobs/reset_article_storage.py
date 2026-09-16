"""Explicit development-only reset for the fixed S3 ``articles/`` namespace."""

import argparse

from app.core import s3
from app.core.config import settings

_CONFIRMATION = "DELETE-ALL-DEVELOPMENT-ARTICLES"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Delete every S3 object under the fixed articles/ prefix."
    )
    parser.add_argument("--confirm", required=True, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not settings.dev_mode:
        parser.error("This command is available only when DEV_MODE=true.")
    if args.confirm != _CONFIRMATION:
        parser.error(f"Confirmation must exactly equal {_CONFIRMATION!r}.")
    # Deliberately fixed: this command never accepts a caller-controlled prefix.
    s3.delete_prefix("articles/")
    print("Deleted the development S3 prefix articles/.")


if __name__ == "__main__":
    main()
