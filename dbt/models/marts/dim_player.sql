select
    p.player_id,
    p.web_name,
    p.first_name || ' ' || p.second_name as full_name,
    p.team_id,
    t.team_name,
    pos.position_short_name              as position,
    p.status
from {{ ref('stg_players') }}   as p
left join {{ ref('stg_teams') }}     as t   on t.team_id = p.team_id
left join {{ ref('stg_positions') }} as pos on pos.position_id = p.position_id
