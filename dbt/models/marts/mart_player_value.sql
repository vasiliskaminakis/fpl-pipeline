-- Which players give the most points per £m? Only players who have actually played.

select
    d.player_id,
    d.web_name,
    d.team_name,
    d.position,
    s.price_m,
    s.total_points,
    s.minutes,
    s.form,
    s.selected_by_percent,
    round(s.total_points / nullif(s.price_m, 0), 2) as points_per_million,
    rank() over (
        partition by d.position
        order by s.total_points / nullif(s.price_m, 0) desc
    )                                               as value_rank_in_position
from {{ ref('stg_players') }} as s
inner join {{ ref('dim_player') }} as d on d.player_id = s.player_id
where s.minutes > 0
