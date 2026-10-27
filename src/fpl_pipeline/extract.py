"""Extract step: pull FPL data and land it in the data lake.

Two layers are written for every run, both partitioned by ingest date:

* data/raw/<endpoint>/ingest_date=YYYY-MM-DD/data.json
    The untouched API response. Immutable source of truth: if a transformation
    has a bug later, we can always rebuild from here.
* data/parquet/<table>/ingest_date=YYYY-MM-DD/data.parquet
    One flat table per entity (players, teams, gameweeks, ...), ready for DuckDB/dbt.

Re-running on the same day overwrites that day's partition, so the step is idempotent.
"""

import argparse
import json
import logging
import os
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd

from . import config
from .client import FPLClient

log = logging.getLogger(__name__)

# Top-level keys we rely on downstream. If the unofficial API drops one, fail loudly.
REQUIRED_BOOTSTRAP_KEYS = {"events", "teams", "elements", "element_types"}

# bootstrap-static key -> table name
BOOTSTRAP_TABLES = {
    "elements": "players",
    "teams": "teams",
    "events": "gameweeks",
    "element_types": "positions",
}


class SchemaDriftError(RuntimeError):
    """Raised when an API response no longer has the shape the pipeline expects."""


def check_schema(payload: Any, required_keys: set[str], name: str) -> None:
    """Fail on missing keys (breaking change); log new keys (informational)."""
    if not isinstance(payload, dict):
        raise SchemaDriftError(f"{name}: expected a JSON object, got {type(payload).__name__}")
    missing = required_keys - payload.keys()
    if missing:
        raise SchemaDriftError(f"{name}: missing expected keys {sorted(missing)}")
    extra = payload.keys() - required_keys
    if extra:
        log.info("%s: additional keys present (ignored): %s", name, sorted(extra))


def _partition_dir(root: Path, name: str, ingest_date: date) -> Path:
    return root / name / f"ingest_date={ingest_date.isoformat()}"


def _atomic_write(path: Path, write_fn) -> None:
    """Write to a temp file then rename, so a crash never leaves a half-written file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    write_fn(tmp)
    os.replace(tmp, path)


def land_raw(
    payload: Any, endpoint: str, ingest_date: date, raw_dir: Path = config.RAW_DIR
) -> Path:
    """Store the untouched API response as JSON."""
    path = _partition_dir(raw_dir, endpoint, ingest_date) / "data.json"

    def _write(tmp: Path) -> None:
        tmp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    _atomic_write(path, _write)
    log.info("Landed raw %s -> %s", endpoint, path)
    return path


def _stringify_nested(df: pd.DataFrame) -> pd.DataFrame:
    """Serialise list/dict columns to JSON strings.

    Parquet handles nested types, but their shape can vary between rows and
    between days. JSON strings are stable, and DuckDB can parse them later.
    """
    df = df.copy()
    for col in df.columns:
        if df[col].map(lambda v: isinstance(v, (list, dict))).any():
            df[col] = df[col].map(
                lambda v: json.dumps(v, ensure_ascii=False) if isinstance(v, (list, dict)) else v
            )
    return df


def write_parquet(
    records: list[dict], table: str, ingest_date: date, parquet_dir: Path = config.PARQUET_DIR
) -> Path:
    """Flatten a list of records to a Parquet file in the date partition."""
    df = _stringify_nested(pd.DataFrame.from_records(records))
    df["ingest_date"] = ingest_date.isoformat()
    path = _partition_dir(parquet_dir, table, ingest_date) / "data.parquet"
    _atomic_write(path, lambda tmp: df.to_parquet(tmp, index=False))
    log.info("Wrote %s: %d rows -> %s", table, len(df), path)
    return path


def run(
    ingest_date: date | None = None,
    client: FPLClient | None = None,
    raw_dir: Path = config.RAW_DIR,
    parquet_dir: Path = config.PARQUET_DIR,
) -> dict[str, int]:
    """Run the full extract. Returns row counts per table (handy for logging/tests)."""
    ingest_date = ingest_date or date.today()
    client = client or FPLClient()
    counts: dict[str, int] = {}

    # 1) bootstrap-static: players, teams, gameweeks, positions
    bootstrap = client.get("bootstrap-static/")
    check_schema(bootstrap, REQUIRED_BOOTSTRAP_KEYS, "bootstrap-static")
    land_raw(bootstrap, "bootstrap-static", ingest_date, raw_dir)
    for key, table in BOOTSTRAP_TABLES.items():
        write_parquet(bootstrap[key], table, ingest_date, parquet_dir)
        counts[table] = len(bootstrap[key])

    # 2) fixtures: a JSON list of all 380 matches of the season
    fixtures = client.get("fixtures/")
    if not isinstance(fixtures, list):
        raise SchemaDriftError("fixtures: expected a JSON list")
    land_raw(fixtures, "fixtures", ingest_date, raw_dir)
    write_parquet(fixtures, "fixtures", ingest_date, parquet_dir)
    counts["fixtures"] = len(fixtures)

    log.info("Extract finished for %s: %s", ingest_date, counts)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract FPL data into the local data lake.")
    parser.add_argument(
        "--date",
        type=date.fromisoformat,
        default=None,
        help="Ingest date (YYYY-MM-DD). Defaults to today.",
    )
    args = parser.parse_args()
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    run(ingest_date=args.date)


if __name__ == "__main__":
    main()
