# FPL Analytics Pipeline

End-to-end ELT pipeline for Fantasy Premier League data: ingest from the public FPL API, land raw
data in a date-partitioned lake, model it in a warehouse, test it, orchestrate it, and serve a
dashboard.

> Status: **Phase 1 (ingestion)** and **Phase 2 (DuckDB + dbt warehouse)** complete.
> Orchestration (Airflow), CI and dashboard are next.

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
make dbt-build  # builds and tests the warehouse models in data/warehouse.duckdb
make top-value  # prints best-value players and easiest fixture runs
make test       # Python unit tests
make lint
```

`make pipeline` runs `extract` and `dbt-build` together.

Output after `make extract`:

```
data/raw/bootstrap-static/ingest_date=YYYY-MM-DD/data.json
data/raw/fixtures/ingest_date=YYYY-MM-DD/data.json
data/parquet/{players,teams,gameweeks,positions,fixtures}/ingest_date=YYYY-MM-DD/data.parquet
```

## Warehouse (dbt + DuckDB)

```
data/parquet (daily snapshots)
   └─ staging (views)   stg_players, stg_teams, stg_positions, stg_gameweeks, stg_fixtures
        └─ marts (tables)  dim_team, dim_player, mart_player_value, mart_fixture_difficulty
```

- **Staging** reads every daily Parquet snapshot, keeps the latest row per entity, fixes types
  (prices from tenths of £m to £m, numeric strings to doubles) and renames columns.
- **Marts** answer the project's questions: which players give the most points per £m, and which
  teams have the easiest next five fixtures.
- **Tests:** unique / not-null / relationships / accepted-values tests on keys and joins, plus a
  singular test that guards against a price-unit change in the API.

## Design decisions

- **Raw layer is immutable JSON.** If a transformation has a bug, everything can be rebuilt from raw.
- **Idempotent by partition.** Re-running a day overwrites that day's folder; no duplicates.
- **Atomic writes.** Write to a temp file, then rename, so a crash never leaves partial files.
- **Schema-drift check.** The FPL API is unofficial and undocumented, so the extractor fails
  loudly if expected keys disappear and logs new ones.
- **Retries with backoff and polite pacing.** The API returns 503s around gameweek updates.
- **Nested fields stored as JSON strings in Parquet.** Keeps the schema stable day to day; parsed
  later in dbt.
- **ELT with DuckDB reading Parquet directly.** No separate load step: dbt views read the lake,
  marts are materialised as tables. The whole warehouse is one local file.
- **Snapshots kept, latest used.** Every day's data is retained in the lake (useful later for price
  history); staging models select the latest row per entity.

## Data source

Public, keyless JSON API at `https://fantasy.premierleague.com/api/` (unofficial). Endpoints used so
far: `bootstrap-static/` and `fixtures/`.
