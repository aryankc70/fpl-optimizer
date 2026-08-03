import pandas as pd
from fpl_optimizer.db.session import SessionLocal
from fpl_optimizer.db.models import PlayerGameweekStat, Player

SEASON = "2025-26"
CSV_URL = f"https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{SEASON}/gws/merged_gw.csv"


def backfill():
    print(f"Downloading {SEASON} gameweek data...")
    df = pd.read_csv(CSV_URL)

    db = SessionLocal()
    try:
        # Only keep rows for players that exist in our current players table —
        # players who've left the league (relegated/retired) aren't useful for this season's predictions
        current_player_ids = {p.id for p in db.query(Player.id).all()}

        loaded, skipped = 0, 0
        for _, row in df.iterrows():
            player_id = int(row["element"])
            if player_id not in current_player_ids:
                skipped += 1
                continue

            stat = PlayerGameweekStat(
                player_id=player_id,
                gameweek_id=int(row["GW"]),
                season=SEASON,
                minutes=int(row.get("minutes", 0)),
                total_points=int(row.get("total_points", 0)),
                goals_scored=int(row.get("goals_scored", 0)),
                assists=int(row.get("assists", 0)),
                clean_sheets=int(row.get("clean_sheets", 0)),
                expected_goals=float(row.get("expected_goals", 0.0) or 0.0),
                expected_assists=float(row.get("expected_assists", 0.0) or 0.0),
                bonus=int(row.get("bonus", 0)),
                value=float(row.get("value", 0)) / 10,
            )
            db.add(stat)
            loaded += 1

        db.commit()
        print(f"Backfilled {loaded} rows, skipped {skipped} (players not on current roster).")
    finally:
        db.close()


if __name__ == "__main__":
    backfill()