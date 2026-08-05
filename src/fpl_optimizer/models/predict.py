import joblib
import pandas as pd
from sqlalchemy import text
from fpl_optimizer.db.session import engine, SessionLocal
from fpl_optimizer.db.models import PlayerPrediction

MODEL_PATH = "models/points_predictor_v1.pkl"

TARGET_SEASON = "2026-27"
TARGET_GAMEWEEK = 1

# How much we trust the season-long average vs. the small recent window.
# Higher SHRINKAGE_K = more weight on the stable season average, less on
# potentially noisy end-of-season form. Treat it as "K virtual games" of
# season-average-strength evidence.
SHRINKAGE_K = 6

FEATURE_COLS = [
    "now_cost",
    "avg_points_last_3",
    "avg_points_last_5",
    "avg_minutes_last_3",
    "avg_xg_last_3",
    "avg_xa_last_3",
    "std_points_last_5",
    "games_in_window_5",
    "pos_DEF",
    "pos_FWD",
    "pos_GKP",
    "pos_MID",
]

LATEST_FORM_QUERY = """
SELECT DISTINCT ON (v.player_id)
    v.player_id,
    p.position,
    p.now_cost,
    v.avg_points_last_3,
    v.avg_points_last_5,
    v.avg_minutes_last_3,
    v.avg_xg_last_3,
    v.avg_xa_last_3,
    v.std_points_last_5,
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
    COUNT(*) AS season_games
FROM player_gameweek_stats
WHERE season = '2025-26'
GROUP BY player_id;
"""


def shrink(recent, season_avg, n_recent, k=SHRINKAGE_K):
    """
    Empirical-Bayes-style shrinkage: blend a small, potentially noisy recent
    sample with a larger, more stable season-long average. The more recent
    games we have (n_recent), the more we trust the recent number; the fewer
    we have, the more we fall back toward the season average.
    """
    return (n_recent * recent + k * season_avg) / (n_recent + k)


def generate_predictions():
    model = joblib.load(MODEL_PATH)

    recent_df = pd.read_sql(text(LATEST_FORM_QUERY), engine)
    season_df = pd.read_sql(text(SEASON_AVG_QUERY), engine)

    df = recent_df.merge(season_df, on="player_id", how="left")

    # Players with no last-season row at all (shouldn't happen given our
    # earlier check, but guard anyway) fall back to their recent numbers unshrunk
    df["season_avg_points"] = df["season_avg_points"].fillna(df["avg_points_last_5"])
    df["season_avg_minutes"] = df["season_avg_minutes"].fillna(df["avg_minutes_last_3"])
    df["season_avg_xg"] = df["season_avg_xg"].fillna(df["avg_xg_last_3"])
    df["season_avg_xa"] = df["season_avg_xa"].fillna(df["avg_xa_last_3"])

    n = df["games_in_window_5"]
    df["avg_points_last_3"] = shrink(df["avg_points_last_3"], df["season_avg_points"], n)
    df["avg_points_last_5"] = shrink(df["avg_points_last_5"], df["season_avg_points"], n)
    df["avg_minutes_last_3"] = shrink(df["avg_minutes_last_3"], df["season_avg_minutes"], n)
    df["avg_xg_last_3"] = shrink(df["avg_xg_last_3"], df["season_avg_xg"], n)
    df["avg_xa_last_3"] = shrink(df["avg_xa_last_3"], df["season_avg_xa"], n)

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