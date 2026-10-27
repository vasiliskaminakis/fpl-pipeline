-- How hard are each team's next 5 fixtures? Lower average difficulty = easier run.
-- (FPL difficulty ratings run from 1 = easiest to 5 = hardest.)

with team_fixtures as (

    select
        gameweek_id,
        kickoff_time,
        home_team_id    as team_id,
        away_team_id    as opponent_id,
        true            as is_home,
        home_difficulty as difficulty
    from {{ ref('stg_fixtures') }}
    where finished = false and gameweek_id is not null

    union all

    select
        gameweek_id,
        kickoff_time,
        away_team_id    as team_id,
        home_team_id    as opponent_id,
        false           as is_home,
        away_difficulty as difficulty
    from {{ ref('stg_fixtures') }}
    where finished = false and gameweek_id is not null

),

numbered as (

    select
        *,
        row_number() over (
            partition by team_id
            order by gameweek_id, kickoff_time
        ) as fixture_number
    from team_fixtures

),

next_five as (

    select * from numbered where fixture_number <= 5

)

select
    t.team_id,
    t.team_name,
    count(*)                      as fixtures_counted,
    round(avg(n.difficulty), 2)   as avg_difficulty,
    min(n.gameweek_id)            as from_gameweek,
    max(n.gameweek_id)            as to_gameweek
from next_five as n
inner join {{ ref('dim_team') }} as t on t.team_id = n.team_id
group by t.team_id, t.team_name
