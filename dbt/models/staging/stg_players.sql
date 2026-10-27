-- One row per player: the most recent daily snapshot.
-- Raw FPL quirks fixed here: prices are in tenths of £m, and form / points_per_game /
-- selected_by_percent arrive as strings.

with snapshots as (

    select * from {{ read_lake('players') }}

),

latest as (

    select *
    from snapshots
    qualify row_number() over (partition by id order by ingest_date desc) = 1

)

select
    id                                       as player_id,
    web_name,
    first_name,
    second_name,
    team                                     as team_id,
    element_type                             as position_id,
    status,
    now_cost / 10.0                          as price_m,
    total_points,
    minutes,
    goals_scored,
    assists,
    clean_sheets,
    cast(form as double)                     as form,
    cast(points_per_game as double)          as points_per_game,
    cast(selected_by_percent as double)      as selected_by_percent,
    cast(ingest_date as date)                as ingest_date
from latest
