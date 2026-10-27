"""Central configuration. Everything can be overridden with environment variables."""

import os
from pathlib import Path

BASE_URL = os.getenv("FPL_BASE_URL", "https://fantasy.premierleague.com/api/")

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.getenv("DATA_DIR", PROJECT_ROOT / "data"))
RAW_DIR = DATA_DIR / "raw"
PARQUET_DIR = DATA_DIR / "parquet"

# Identify ourselves politely; the API is unofficial and publishes no rate limit.
USER_AGENT = "fpl-pipeline/0.1 (personal portfolio project)"
REQUEST_TIMEOUT_SECONDS = 30
REQUEST_DELAY_SECONDS = 0.5
MAX_RETRIES = 5
