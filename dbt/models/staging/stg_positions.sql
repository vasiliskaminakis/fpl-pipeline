-- One row per position (GKP, DEF, MID, FWD).

with snapshots as (

    select * from {{ read_lake('positions') }}

),

latest as (

    select *
    from snapshots
    qualify row_number() over (partition by id order by ingest_date desc) = 1

)

select
    id                  as position_id,
    singular_name       as position_name,
    singular_name_short as position_short_name
from latest
