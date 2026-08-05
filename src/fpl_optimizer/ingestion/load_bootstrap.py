from datetime import datetime
from fpl_optimizer.ingestion.fpl_client import FPLClient
from fpl_optimizer.db.session import SessionLocal
from fpl_optimizer.db.models import Team, Player, Gameweek

POSITION_MAP = {1: "GKP", 2: "DEF", 3: "MID", 4: "FWD"}


def load_teams(db, data: dict):
    for t in data["teams"]:
        team = db.get(Team, t["id"])
        if team is None:
            team = Team(id=t["id"])
        team.name = t["name"]
        team.short_name = t["short_name"]
        team.strength_overall_home = t.get("strength_overall_home") or 0
        team.strength_overall_away = t.get("strength_overall_away") or 0
        team.strength_attack_home = t.get("strength_attack_home") or 0
        team.strength_attack_away = t.get("strength_attack_away") or 0
        team.strength_defence_home = t.get("strength_defence_home") or 0
        team.strength_defence_away = t.get("strength_defence_away") or 0
        db.add(team)
    db.commit()
    print(f"Loaded {len(data['teams'])} teams.")


def load_players(db, data: dict):
    for p in data["elements"]:
        player = db.get(Player, p["id"])
        if player is None:
            player = Player(id=p["id"])
        player.first_name = p["first_name"]
        player.second_name = p["second_name"]
        player.web_name = p["web_name"]
        player.team_id = p["team"]
        player.position = POSITION_MAP.get(p["element_type"], "UNK")
        player.now_cost = p["now_cost"] / 10  # FPL stores price as tenths (e.g. 105 -> 10.5)
        player.status = p.get("status", "a")
        player.chance_of_playing_next_round = p.get("chance_of_playing_next_round")
        db.add(player)
    db.commit()
    print(f"Loaded {len(data['elements'])} players.")


def load_gameweeks(db, data: dict):
    for gw in data["events"]:
        gameweek = db.get(Gameweek, gw["id"])
        if gameweek is None:
            gameweek = Gameweek(id=gw["id"])
        gameweek.name = gw["name"]
        gameweek.deadline_time = datetime.fromisoformat(gw["deadline_time"].replace("Z", "+00:00"))
        gameweek.is_current = gw.get("is_current", False)
        gameweek.is_finished = gw.get("finished", False)
        db.add(gameweek)
    db.commit()
    print(f"Loaded {len(data['events'])} gameweeks.")


def run():
    client = FPLClient()
    data = client.get_bootstrap_static()

    db = SessionLocal()
    try:
        load_teams(db, data)
        load_players(db, data)
        load_gameweeks(db, data)
    finally:
        db.close()


if __name__ == "__main__":
    run()