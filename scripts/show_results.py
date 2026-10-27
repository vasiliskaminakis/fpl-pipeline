"""Print a quick summary from the warehouse so you can see the pipeline's output."""

import os
from pathlib import Path

import duckdb

DB_PATH = Path(
    os.getenv("DUCKDB_PATH", Path(__file__).resolve().parents[1] / "data" / "warehouse.duckdb")
)


def main() -> None:
    con = duckdb.connect(str(DB_PATH), read_only=True)

    print("\nTop 10 value players (points per £m, min. 1 minute played)\n")
    print(
        con.sql(
            """
            select web_name, team_name, position, price_m, total_points, points_per_million
            from mart_player_value
            order by points_per_million desc
            limit 10
            """
        )
        .df()
        .to_string(index=False)
    )

    print("\nEasiest next-5 fixture runs\n")
    print(
        con.sql(
            """
            select team_name, avg_difficulty, from_gameweek, to_gameweek
            from mart_fixture_difficulty
            order by avg_difficulty
            limit 5
            """
        )
        .df()
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
