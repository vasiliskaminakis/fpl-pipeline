-- One row per fixture: the most recent daily snapshot.
-- gameweek_id is NULL for postponed or unscheduled matches.

with snapshots as (

    select * from {{ read_lake('fixtures') }}

),

latest as (

    select *
    from snapshots
    qualify row_number() over (partition by id order by ingest_date desc) = 1

)

select
    id                                   as fixture_id,
    cast(event as integer)               as gameweek_id,
    team_h                               as home_team_id,
    team_a                               as away_team_id,
    cast(kickoff_time as timestamp)      as kickoff_time,
    finished,
    cast(team_h_score as integer)        as home_score,
    cast(team_a_score as integer)        as away_score,
    team_h_difficulty                    as home_difficulty,
    team_a_difficulty                    as away_difficulty
from latest
