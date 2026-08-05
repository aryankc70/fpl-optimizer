import unicodedata
import pandas as pd
from fpl_optimizer.db.session import SessionLocal
from fpl_optimizer.db.models import PlayerGameweekStat, Player

SEASON = "2025-26"
CSV_URL = f"https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{SEASON}/gws/merged_gw.csv"

RAW_COLS = [
    "name", "GW", "minutes", "total_points", "goals_scored", "assists",
    "clean_sheets", "expected_goals", "expected_assists", "bonus", "value",
]


def normalize_name(name: str) -> str:
    """
    Strip accents/diacritics and lowercase, so 'Ødegaard' and 'Odegaard'
    (or 'Raúl' and 'Raul') match consistently across sources that encode
    names differently.
    """
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_name = nfkd.encode("ascii", "ignore").decode("ascii")
    return ascii_name.strip().lower()


def build_name_lookup(db) -> dict[str, int]:
    """Maps normalized 'first last' name -> current player_id."""
    players = db.query(Player).all()
    lookup = {}
    for p in players:
        full_name = normalize_name(f"{p.first_name} {p.second_name}")
        lookup[full_name] = p.id
    return lookup


def clean_and_aggregate(df: pd.DataFrame) -> pd.DataFrame:
    available_cols = [c for c in RAW_COLS if c in df.columns]
    df = df[available_cols].copy()

    before = len(df)
    df = df.drop_duplicates()
    exact_dupes_removed = before - len(df)

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

    grouped = df.groupby(["name", "GW"], as_index=False).agg(agg_funcs)

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
        name_lookup = build_name_lookup(db)

        loaded, skipped, unmatched_names = 0, 0, set()
        for _, row in df.iterrows():
            norm_name = normalize_name(row["name"])
            player_id = name_lookup.get(norm_name)

            if player_id is None:
                skipped += 1
                unmatched_names.add(row["name"])
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
        print(f"Backfilled {loaded} rows, skipped {skipped} (name not matched to current roster).")
        print(f"Unique unmatched player names: {len(unmatched_names)}")
        if unmatched_names:
            sample = sorted(unmatched_names)[:15]
            print(f"Sample unmatched names: {sample}")
    finally:
        db.close()


if __name__ == "__main__":
    backfill()