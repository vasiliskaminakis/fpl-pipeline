import json
from datetime import date

import pandas as pd
import pytest

from fpl_pipeline import extract

DAY = date(2026, 10, 27)


class FakeClient:
    """Stands in for FPLClient so tests never touch the network."""

    def __init__(self, bootstrap, fixtures):
        self._data = {"bootstrap-static/": bootstrap, "fixtures/": fixtures}

    def get(self, path, params=None):
        return self._data[path]


@pytest.fixture
def bootstrap():
    return {
        "elements": [
            {
                "id": 1,
                "web_name": "Saka",
                "now_cost": 100,
                "team": 1,
                "chance_of_playing_next_round": None,
            },
            {
                "id": 2,
                "web_name": "Haaland",
                "now_cost": 150,
                "team": 2,
                "chance_of_playing_next_round": 75,
            },
        ],
        "teams": [{"id": 1, "name": "Arsenal"}, {"id": 2, "name": "Man City"}],
        "events": [
            {
                "id": 1,
                "name": "Gameweek 1",
                "chip_plays": [{"chip_name": "bboost", "num_played": 5}],
            }
        ],
        "element_types": [{"id": 1, "singular_name": "Goalkeeper"}],
        "game_settings": {"squad_size": 15},
    }


@pytest.fixture
def fixtures():
    return [
        {"id": 1, "event": 1, "team_h": 1, "team_a": 2, "stats": [{"identifier": "goals_scored"}]}
    ]


def test_check_schema_passes_and_ignores_extra_keys(bootstrap):
    extract.check_schema(bootstrap, extract.REQUIRED_BOOTSTRAP_KEYS, "bootstrap-static")


def test_check_schema_raises_on_missing_key(bootstrap):
    del bootstrap["elements"]
    with pytest.raises(extract.SchemaDriftError, match="elements"):
        extract.check_schema(bootstrap, extract.REQUIRED_BOOTSTRAP_KEYS, "bootstrap-static")


def test_check_schema_raises_on_wrong_type():
    with pytest.raises(extract.SchemaDriftError):
        extract.check_schema([], {"a"}, "x")


def test_land_raw_writes_partitioned_json(tmp_path):
    path = extract.land_raw({"a": 1}, "bootstrap-static", DAY, raw_dir=tmp_path)
    assert path == tmp_path / "bootstrap-static" / "ingest_date=2026-10-27" / "data.json"
    assert json.loads(path.read_text()) == {"a": 1}


def test_write_parquet_serialises_nested_columns(tmp_path):
    records = [{"id": 1, "stats": [{"x": 1}]}, {"id": 2, "stats": []}]
    path = extract.write_parquet(records, "fixtures", DAY, parquet_dir=tmp_path)
    df = pd.read_parquet(path)
    assert list(df["id"]) == [1, 2]
    assert json.loads(df.loc[0, "stats"]) == [{"x": 1}]
    assert (df["ingest_date"] == "2026-10-27").all()


def test_run_end_to_end_and_idempotent(tmp_path, bootstrap, fixtures):
    client = FakeClient(bootstrap, fixtures)
    kwargs = {"raw_dir": tmp_path / "raw", "parquet_dir": tmp_path / "parquet"}

    counts_1 = extract.run(ingest_date=DAY, client=client, **kwargs)
    counts_2 = extract.run(ingest_date=DAY, client=client, **kwargs)  # same day again

    expected = {"players": 2, "teams": 2, "gameweeks": 1, "positions": 1, "fixtures": 1}
    assert counts_1 == counts_2 == expected

    # Re-running the same day overwrites the partition instead of duplicating rows
    players = pd.read_parquet(tmp_path / "parquet" / "players" / "ingest_date=2026-10-27")
    assert len(players) == 2
    assert (tmp_path / "raw" / "bootstrap-static" / "ingest_date=2026-10-27" / "data.json").exists()
