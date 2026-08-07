import joblib
import pandas as pd
from sqlalchemy import text

from fpl_optimizer.db.models import Fixture, PlayerPrediction
from fpl_optimizer.db.session import SessionLocal, engine
from fpl_optimizer.features.clean_sheet_model import estimate_clean_sheet

MODEL_PATH = "models/points_predictor_v1.pkl"

TARGET_SEASON = "2026-27"
TARGET_GAMEWEEK = 1

SHRINKAGE_K = 6
LEAGUE_AVG_GOALS_CONCEDED = 1.375

FEATURE_COLS = [
    "now_cost",
    "avg_points_last_3",
    "avg_points_last_5",
    "avg_minutes_last_3",
    "avg_xg_last_3",
    "avg_xa_last_3",
    "std_points_last_5",
    "games_in_window_5",
    "team_avg_goals_conceded_last_3",
    "pos_DEF",
    "pos_FWD",
    "pos_GKP",
    "pos_MID",
    "avg_dc_last_3",
]

LATEST_FORM_QUERY = """
SELECT DISTINCT ON (v.player_id)
    v.player_id,
    p.team_id,
    p.position,
    p.now_cost,
    v.avg_points_last_3,
    v.avg_points_last_5,
    v.avg_minutes_last_3,
    v.avg_xg_last_3,
    v.avg_xa_last_3,
    v.std_points_last_5,
    v.avg_dc_last_3,
    v.games_in_window_5
FROM player_rolling_form v
JOIN players p ON p.id = v.player_id
WHERE v.games_in_window_5 >= 3
ORDER BY v.player_id, v.season DESC, v.gameweek_id DESC;
"""

SEASON_AVG_QUERY = """
SELECT
    player_id,
    AVG(total_points) AS season_avg_points,
    AVG(minutes) AS season_avg_minutes,
    AVG(expected_goals) AS season_avg_xg,
    AVG(expected_assists) AS season_avg_xa,
    AVG(defensive_contribution) AS season_avg_dc,
    COUNT(*) AS season_games
FROM player_gameweek_stats
WHERE season = '2025-26'
GROUP BY player_id;
"""


def shrink(recent, season_avg, n_recent, k=SHRINKAGE_K):
    return (n_recent * recent + k * season_avg) / (n_recent + k)


def get_gw1_opponent(team_id: int) -> tuple[int, bool] | None:
    db = SessionLocal()
    try:
        fixture = (
            db.query(Fixture)
            .filter(Fixture.gameweek_id == TARGET_GAMEWEEK)
            .filter((Fixture.team_h_id == team_id) | (Fixture.team_a_id == team_id))
            .first()
        )
        if fixture is None:
            return None
        if fixture.team_h_id == team_id:
            return fixture.team_a_id, True
        return fixture.team_h_id, False
    finally:
        db.close()


def build_team_defense_map(team_ids) -> dict:
    team_defense_map = {}
    for team_id in team_ids:
        team_id = int(team_id)
        opponent_info = get_gw1_opponent(team_id)
        if opponent_info is None:
            team_defense_map[team_id] = LEAGUE_AVG_GOALS_CONCEDED
        else:
            opponent_id, is_home = opponent_info
            est = estimate_clean_sheet(
                defending_team_id=team_id,
                opponent_team_id=opponent_id,
                defending_team_is_home=is_home,
            )
            team_defense_map[team_id] = est.expected_goals_conceded
    return team_defense_map


def generate_predictions():
    model = joblib.load(MODEL_PATH)

    recent_df = pd.read_sql(text(LATEST_FORM_QUERY), engine)
    season_df = pd.read_sql(text(SEASON_AVG_QUERY), engine)

    df = recent_df.merge(season_df, on="player_id", how="left")

    df["season_avg_points"] = df["season_avg_points"].fillna(df["avg_points_last_5"])
    df["season_avg_minutes"] = df["season_avg_minutes"].fillna(df["avg_minutes_last_3"])
    df["season_avg_xg"] = df["season_avg_xg"].fillna(df["avg_xg_last_3"])
    df["season_avg_xa"] = df["season_avg_xa"].fillna(df["avg_xa_last_3"])
    df["season_avg_dc"] = df["season_avg_dc"].fillna(df["avg_dc_last_3"])

    n = df["games_in_window_5"]
    df["avg_points_last_3"] = shrink(df["avg_points_last_3"], df["season_avg_points"], n)
    df["avg_points_last_5"] = shrink(df["avg_points_last_5"], df["season_avg_points"], n)
    df["avg_minutes_last_3"] = shrink(df["avg_minutes_last_3"], df["season_avg_minutes"], n)
    df["avg_xg_last_3"] = shrink(df["avg_xg_last_3"], df["season_avg_xg"], n)
    df["avg_xa_last_3"] = shrink(df["avg_xa_last_3"], df["season_avg_xa"], n)
    df["avg_dc_last_3"] = shrink(df["avg_dc_last_3"], df["season_avg_dc"], n)

    team_ids = df["team_id"].unique()
    team_defense_map = build_team_defense_map(team_ids)
    df["team_avg_goals_conceded_last_3"] = df["team_id"].map(team_defense_map)

    df = pd.get_dummies(df, columns=["position"], prefix="pos")
    for col in FEATURE_COLS:
        if col not in df.columns:
            df[col] = 0

    df["predicted_points"] = model.predict(df[FEATURE_COLS])

    db = SessionLocal()
    try:
        db.query(PlayerPrediction).filter_by(
            season=TARGET_SEASON, gameweek_id=TARGET_GAMEWEEK
        ).delete()

        for _, row in df.iterrows():
            db.add(PlayerPrediction(
                player_id=int(row["player_id"]),
                season=TARGET_SEASON,
                gameweek_id=TARGET_GAMEWEEK,
                predicted_points=float(row["predicted_points"]),
            ))
        db.commit()
        print(f"Generated predictions for {len(df)} players (season={TARGET_SEASON}, GW={TARGET_GAMEWEEK}).")
    finally:
        db.close()


if __name__ == "__main__":
    generate_predictions()