# FPL Analytics Pipeline

End-to-end ELT pipeline for Fantasy Premier League data: ingest from the public FPL API, land raw
data in a date-partitioned lake, model it in a warehouse, test it, orchestrate it, and serve a
dashboard.

> Status: **Phase 1 – ingestion** complete. Warehouse (DuckDB + dbt), orchestration (Airflow),
> CI and dashboard are next.

## Planned architecture

```
FPL API ──► Python extract ──► raw JSON + Parquet (data lake, by ingest_date)
                                     │
                                     ▼
                         DuckDB ◄── dbt (staging → marts, tested)
                                     │
                         Airflow orchestrates ─► Streamlit dashboard
```

## Quickstart (macOS)

```bash
make setup      # creates .venv and installs the package
make extract    # pulls today's data into data/raw and data/parquet
make test
make lint
```

Output after `make extract`:

```
data/raw/bootstrap-static/ingest_date=YYYY-MM-DD/data.json
data/raw/fixtures/ingest_date=YYYY-MM-DD/data.json
data/parquet/{players,teams,gameweeks,positions,fixtures}/ingest_date=YYYY-MM-DD/data.parquet
```

## Design decisions

- **Raw layer is immutable JSON.** If a transformation has a bug, everything can be rebuilt from raw.
- **Idempotent by partition.** Re-running a day overwrites that day's folder; no duplicates.
- **Atomic writes.** Write to a temp file, then rename, so a crash never leaves partial files.
- **Schema-drift check.** The FPL API is unofficial and undocumented, so the extractor fails
  loudly if expected keys disappear and logs new ones.
- **Retries with backoff and polite pacing.** The API returns 503s around gameweek updates.
- **Nested fields stored as JSON strings in Parquet.** Keeps the schema stable day to day; parsed
  later in dbt.

## Data source

Public, keyless JSON API at `https://fantasy.premierleague.com/api/` (unofficial). Endpoints used so
far: `bootstrap-static/` and `fixtures/`.
