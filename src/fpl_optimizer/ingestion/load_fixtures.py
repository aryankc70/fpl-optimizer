from datetime import datetime

from fpl_optimizer.db.models import Fixture
from fpl_optimizer.db.session import SessionLocal
from fpl_optimizer.ingestion.fpl_client import FPLClient


def load_fixtures(db, fixtures: list[dict]):
    count = 0
    for f in fixtures:
        fixture = db.get(Fixture, f["id"])
        if fixture is None:
            fixture = Fixture(id=f["id"])

        fixture.gameweek_id = f.get("event")  # FPL calls gameweek "event" here
        fixture.team_h_id = f["team_h"]
        fixture.team_a_id = f["team_a"]
        fixture.team_h_difficulty = f.get("team_h_difficulty", 0)
        fixture.team_a_difficulty = f.get("team_a_difficulty", 0)
        fixture.finished = f.get("finished", False)
        fixture.team_h_score = f.get("team_h_score")
        fixture.team_a_score = f.get("team_a_score")

        kickoff = f.get("kickoff_time")
        fixture.kickoff_time = (
            datetime.fromisoformat(kickoff) if kickoff else None
        )

        db.add(fixture)
        count += 1
    db.commit()
    print(f"Loaded {count} fixtures.")


def run():
    client = FPLClient()
    fixtures = client.get_fixtures()

    db = SessionLocal()
    try:
        load_fixtures(db, fixtures)
    finally:
        db.close()


if __name__ == "__main__":
    run()