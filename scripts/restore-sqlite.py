"""Restore a SQLite backup to a new or explicitly approved destination."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def restore_database(source_path: Path, destination_path: Path, *, force: bool) -> None:
    if not source_path.is_file():
        raise FileNotFoundError(f"SQLite backup does not exist: {source_path}")
    if destination_path.exists() and not force:
        raise FileExistsError(
            f"SQLite restore target already exists; pass --force to replace it: {destination_path}"
        )

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(f"file:{source_path.resolve()}?mode=ro", uri=True) as source:
        with sqlite3.connect(destination_path) as destination:
            source.backup(destination)
            integrity = destination.execute("PRAGMA integrity_check").fetchone()
            if integrity != ("ok",):
                raise RuntimeError(f"SQLite restore integrity check failed: {integrity}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="path to a verified SQLite backup")
    parser.add_argument("destination", type=Path, help="restore target path")
    parser.add_argument(
        "--force",
        action="store_true",
        help="allow replacing an existing restore target",
    )
    args = parser.parse_args()
    restore_database(args.source, args.destination, force=args.force)
    print(f"SQLite database restored: {args.destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
