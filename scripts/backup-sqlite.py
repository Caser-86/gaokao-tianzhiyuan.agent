"""Create a consistent SQLite backup using Python's standard-library backup API."""

from __future__ import annotations

import argparse
import sqlite3
from pathlib import Path


def backup_database(source_path: Path, destination_path: Path) -> None:
    if not source_path.is_file():
        raise FileNotFoundError(f"SQLite source does not exist: {source_path}")
    if destination_path.exists():
        raise FileExistsError(f"SQLite backup already exists: {destination_path}")

    destination_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(f"file:{source_path.resolve()}?mode=ro", uri=True) as source:
        with sqlite3.connect(destination_path) as destination:
            source.backup(destination)
            integrity = destination.execute("PRAGMA integrity_check").fetchone()
            if integrity != ("ok",):
                raise RuntimeError(f"SQLite backup integrity check failed: {integrity}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="path to the live SQLite database")
    parser.add_argument("destination", type=Path, help="new backup path")
    args = parser.parse_args()
    backup_database(args.source, args.destination)
    print(f"SQLite backup created: {args.destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
