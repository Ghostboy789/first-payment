"""Build the local marts and regenerate the aggregate site data."""

import argparse
import fcntl
import os
import subprocess
import sys
from pathlib import Path

from analysis import analyze
from config import DUCKDB_PATH, PARQUET_PATH, REPO_ROOT, ZIP_PATH
from extract import extract
from render_site import render


def build_marts(parquet, database):
    subprocess.run(
        [
            str(Path(sys.executable).with_name("dbt")),
            "build",
            "--project-dir",
            "dbt",
            "--profiles-dir",
            "dbt",
        ],
        cwd=REPO_ROOT,
        env={
            **os.environ,
            "FIRST_PAYMENT_PARQUET_PATH": str(parquet.resolve()),
            "FIRST_PAYMENT_DUCKDB_PATH": str(database.resolve()),
            "DBT_SEND_ANONYMOUS_USAGE_STATS": "false",
        },
        check=True,
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path, nargs="?", default=ZIP_PATH)
    args = parser.parse_args()
    if not args.archive.is_file():
        parser.error(f"Archive not found: {args.archive}")
    PARQUET_PATH.parent.mkdir(exist_ok=True)
    with PARQUET_PATH.with_name(".build.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        extract(args.archive, PARQUET_PATH)
        build_marts(PARQUET_PATH, DUCKDB_PATH)
        render(analyze(DUCKDB_PATH))


if __name__ == "__main__":
    main()
