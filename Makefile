.PHONY: setup extract test lint format clean

PY := .venv/bin/python

setup:
	python3 -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -e ".[dev]"

extract:
	$(PY) -m fpl_pipeline.extract

test:
	$(PY) -m pytest -q

lint:
	.venv/bin/ruff check .

format:
	.venv/bin/ruff format .

clean:
	rm -rf data/raw data/parquet .pytest_cache .ruff_cache
