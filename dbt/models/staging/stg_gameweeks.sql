-- One row per gameweek ("event" in the FPL API): the most recent daily snapshot.

with snapshots as (

    select * from {{ read_lake('gameweeks') }}

),

latest as (

    select *
    from snapshots
    qualify row_number() over (partition by id order by ingest_date desc) = 1

)

select
    id                               as gameweek_id,
    name                             as gameweek_name,
    cast(deadline_time as timestamp) as deadline_time,
    finished,
    is_current,
    is_next
from latest
