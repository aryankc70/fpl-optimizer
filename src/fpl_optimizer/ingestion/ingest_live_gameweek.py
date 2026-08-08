import requests
from sqlalchemy import text

from fpl_optimizer.db.models import PlayerGameweekStat
from fpl_optimizer.db.session import SessionLocal, engine

SEASON = "2026-27"
LIVE_URL_TEMPLATE = "https://fantasy.premierleague.com/api/event/{gw}/live/"


def get_finished_ungested_gameweeks(db) -> list[int]:
    """
    Finds gameweeks that are marked finished in our `gameweeks` table but
    don't yet have any rows in `player_gameweek_stats` for the CURRENT
    season — i.e. results we should ingest but haven't yet.
    """
    query = text("""
        SELECT g.id
        FROM gameweeks g
        WHERE g.is_finished = TRUE
        AND NOT EXISTS (
            SELECT 1 FROM player_gameweek_stats s
            WHERE s.season = :season AND s.gameweek_id = g.id
        )
        ORDER BY g.id;
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"season": SEASON}).fetchall()
    return [r.id for r in rows]


def ingest_gameweek(db, gameweek_id: int, current_player_ids: set[int]):
    resp = requests.get(LIVE_URL_TEMPLATE.format(gw=gameweek_id))
    resp.raise_for_status()
    data = resp.json()

    inserted, skipped = 0, 0
    for element in data["elements"]:
        player_id = element["id"]
        if player_id not in current_player_ids:
            skipped += 1
            continue

        stats = element["stats"]

        existing = db.query(PlayerGameweekStat).filter_by(
            player_id=player_id, season=SEASON, gameweek_id=gameweek_id
        ).first()
        if existing is not None:
            continue  # already ingested this gameweek for this player, skip

        db.add(PlayerGameweekStat(
            player_id=player_id,
            gameweek_id=gameweek_id,
            season=SEASON,
            minutes=stats.get("minutes", 0),
            total_points=stats.get("total_points", 0),
            goals_scored=stats.get("goals_scored", 0),
            assists=stats.get("assists", 0),
            clean_sheets=stats.get("clean_sheets", 0),
            expected_goals=stats.get("expected_goals", 0.0) or 0.0,
            expected_assists=stats.get("expected_assists", 0.0) or 0.0,
            bonus=stats.get("bonus", 0),
            clearances_blocks_interceptions=stats.get("clearances_blocks_interceptions", 0),
            tackles=stats.get("tackles", 0),
            recoveries=stats.get("recoveries", 0),
            defensive_contribution=stats.get("defensive_contribution", 0),
            value=0.0,  # populated separately from current player price; see note below
        ))
        inserted += 1

    return inserted, skipped


def run():
    db = SessionLocal()
    try:
        from fpl_optimizer.db.models import Player
        current_player_ids = {p.id for p in db.query(Player.id).all()}

        gameweeks_to_ingest = get_finished_ungested_gameweeks(db)
        if not gameweeks_to_ingest:
            print("No new finished gameweeks to ingest.")
            return

        for gw in gameweeks_to_ingest:
            inserted, skipped = ingest_gameweek(db, gw, current_player_ids)
            db.commit()
            print(f"GW{gw}: ingested {inserted} player-gameweek rows, skipped {skipped}.")
    finally:
        db.close()


if __name__ == "__main__":
    run()