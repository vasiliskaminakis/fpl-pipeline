.PHONY: setup extract dbt-build pipeline top-value test lint format clean

PY := .venv/bin/python
DBT := ../.venv/bin/dbt

setup:
	python3 -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"

extract:
	$(PY) -m fpl_pipeline.extract

# Build + test every dbt model (run from inside dbt/ so relative paths resolve)
dbt-build:
	cd dbt && $(DBT) build --profiles-dir .

# Whole pipeline: API -> data lake -> warehouse
pipeline: extract dbt-build

# Print the best-value players and the easiest fixture runs
top-value:
	$(PY) scripts/show_results.py

test:
	$(PY) -m pytest -q

lint:
	.venv/bin/ruff check .

format:
	.venv/bin/ruff format .

clean:
	rm -rf data/raw data/parquet data/warehouse.duckdb dbt/target dbt/logs .pytest_cache .ruff_cache
