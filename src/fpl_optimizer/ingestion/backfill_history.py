import pandas as pd
from fpl_optimizer.db.session import SessionLocal
from fpl_optimizer.db.models import PlayerGameweekStat, Player

SEASON = "2025-26"
CSV_URL = f"https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{SEASON}/gws/merged_gw.csv"

RAW_COLS = [
    "element", "GW", "minutes", "total_points", "goals_scored", "assists",
    "clean_sheets", "expected_goals", "expected_assists", "bonus", "value",
]


def clean_and_aggregate(df: pd.DataFrame) -> pd.DataFrame:
    # Keep only the columns we care about, so drop_duplicates checks the
    # right thing (full-row duplicates on the fields that matter to us)
    available_cols = [c for c in RAW_COLS if c in df.columns]
    df = df[available_cols].copy()

    before = len(df)
    df = df.drop_duplicates()
    exact_dupes_removed = before - len(df)

    # Whatever duplicate (element, GW) pairs remain now are GENUINE double
    # gameweeks — different fixtures with different stats. Sum the additive
    # stats across fixtures; keep the latest price seen that gameweek.
    agg_funcs = {
        "minutes": "sum",
        "total_points": "sum",
        "goals_scored": "sum",
        "assists": "sum",
        "clean_sheets": "sum",
        "expected_goals": "sum",
        "expected_assists": "sum",
        "bonus": "sum",
        "value": "last",
    }
    agg_funcs = {k: v for k, v in agg_funcs.items() if k in df.columns}

    grouped = df.groupby(["element", "GW"], as_index=False).agg(agg_funcs)

    dgw_rows_merged = before - exact_dupes_removed - len(grouped)
    print(f"Removed {exact_dupes_removed} exact duplicate rows.")
    print(f"Merged {dgw_rows_merged} rows from genuine double-gameweeks.")

    return grouped


def backfill():
    print(f"Downloading {SEASON} gameweek data...")
    raw_df = pd.read_csv(CSV_URL)
    df = clean_and_aggregate(raw_df)

    db = SessionLocal()
    try:
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