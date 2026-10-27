-- One row per Premier League team: the most recent daily snapshot.

with snapshots as (

    select * from {{ read_lake('teams') }}

),

latest as (

    select *
    from snapshots
    qualify row_number() over (partition by id order by ingest_date desc) = 1

)

select
    id                         as team_id,
    name                       as team_name,
    short_name                 as team_short_name,
    strength,
    cast(ingest_date as date)  as ingest_date
from latest
