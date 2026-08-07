import pandas as pd
from sqlalchemy import text
from fpl_optimizer.db.session import engine

QUERY = """
SELECT
    v.player_id,
    v.season,
    v.gameweek_id,
    p.position,
    p.now_cost,
    v.avg_points_last_3,
    v.avg_points_last_5,
    v.avg_minutes_last_3,
    v.avg_xg_last_3,
    v.avg_xa_last_3,
    v.std_points_last_5,
    v.games_in_window_5,
    v.avg_dc_last_3,
    COALESCE(tdf.avg_goals_conceded_last_3, 1.375) AS team_avg_goals_conceded_last_3,
    v.total_points AS target
FROM player_rolling_form v
JOIN players p ON p.id = v.player_id
LEFT JOIN team_defensive_form tdf
    ON tdf.team_id = p.team_id
    AND tdf.season = v.season
    AND tdf.gameweek_id = v.gameweek_id
WHERE v.games_in_window_5 >= 3
ORDER BY v.season, v.gameweek_id;
"""


def load_training_data() -> pd.DataFrame:
    df = pd.read_sql(text(QUERY), engine)
    df = pd.get_dummies(df, columns=["position"], prefix="pos")
    return df


if __name__ == "__main__":
    df = load_training_data()
    print(df.shape)
    print(df.head())