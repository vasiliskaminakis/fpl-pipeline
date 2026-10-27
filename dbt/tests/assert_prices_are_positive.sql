-- A dbt "singular" test: it passes when this query returns zero rows.
-- Catches a unit change in the API (e.g. prices suddenly not in tenths of £m).

select player_id, web_name, price_m
from {{ ref('stg_players') }}
where price_m <= 0 or price_m > 25
