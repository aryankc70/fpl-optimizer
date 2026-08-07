import unicodedata
import pandas as pd
from sqlalchemy import text
from fpl_optimizer.db.session import SessionLocal, engine
from fpl_optimizer.db.models import Team

SEASON = "2025-26"
FIXTURES_URL = f"https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{SEASON}/fixtures.csv"
TEAMS_URL = f"https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/{SEASON}/teams.csv"


def normalize_name(name: str) -> str:
    nfkd = unicodedata.normalize("NFKD", name)
    return nfkd.encode("ascii", "ignore").decode("ascii").strip().lower()


def build_team_lookup(db) -> dict[str, int]:
    """Maps normalized CURRENT-season team name -> current team_id."""
    teams = db.query(Team).all()
    return {normalize_name(t.name): t.id for t in teams}


def build_historical_id_to_name(season: str) -> dict[int, str]:
    """Maps LAST season's numeric team id (as used in fixtures.csv) -> team name."""
    teams_df = pd.read_csv(TEAMS_URL)
    return {int(row["id"]): row["name"] for _, row in teams_df.iterrows()}


def backfill_fixtures():
    print(f"Downloading {SEASON} fixture results...")
    fixtures_df = pd.read_csv(FIXTURES_URL)
    fixtures_df = fixtures_df[fixtures_df["finished"] == True].copy()

    historical_id_to_name = build_historical_id_to_name(SEASON)

    db = SessionLocal()
    try:
        team_lookup = build_team_lookup(db)
        rows = []
        unmatched = set()

        for _, row in fixtures_df.iterrows():
            home_hist_id = int(row["team_h"])
            away_hist_id = int(row["team_a"])

            home_name = historical_id_to_name.get(home_hist_id)
            away_name = historical_id_to_name.get(away_hist_id)

            home_id = team_lookup.get(normalize_name(home_name)) if home_name else None
            away_id = team_lookup.get(normalize_name(away_name)) if away_name else None

            if home_id is None:
                unmatched.add(home_name or f"unknown_id_{home_hist_id}")
            if away_id is None:
                unmatched.add(away_name or f"unknown_id_{away_hist_id}")

            if home_id is None or away_id is None:
                continue

            rows.append({
                "season": SEASON,
                "gameweek_id": int(row["event"]) if pd.notna(row["event"]) else None,
                "team_h_id": home_id,
                "team_a_id": away_id,
                "team_h_score": int(row["team_h_score"]),
                "team_a_score": int(row["team_a_score"]),
            })

        print(f"Matched {len(rows)} fixtures, {len(unmatched)} unmatched team names: {unmatched}")

        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS historical_fixture_results (
                    id SERIAL PRIMARY KEY,
                    season VARCHAR(10),
                    gameweek_id INTEGER,
                    team_h_id INTEGER REFERENCES teams(id),
                    team_a_id INTEGER REFERENCES teams(id),
                    team_h_score INTEGER,
                    team_a_score INTEGER
                );
            """))
            conn.execute(text("DELETE FROM historical_fixture_results WHERE season = :season"), {"season": SEASON})
            for r in rows:
                conn.execute(text("""
                    INSERT INTO historical_fixture_results
                    (season, gameweek_id, team_h_id, team_a_id, team_h_score, team_a_score)
                    VALUES (:season, :gameweek_id, :team_h_id, :team_a_id, :team_h_score, :team_a_score)
                """), r)

        print(f"Backfilled {len(rows)} historical fixture results.")
    finally:
        db.close()


if __name__ == "__main__":
    backfill_fixtures()