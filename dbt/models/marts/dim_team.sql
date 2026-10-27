select
    team_id,
    team_name,
    team_short_name,
    strength
from {{ ref('stg_teams') }}
