from dataclasses import dataclass
from ortools.sat.python import cp_model
from sqlalchemy import text
from fpl_optimizer.db.session import engine

BUDGET = 1000
SQUAD_SIZE = 15
POSITION_QUOTAS = {"GKP": 2, "DEF": 5, "MID": 5, "FWD": 3}
MAX_PER_CLUB = 3

QUERY = """
SELECT
    p.id AS player_id,
    p.web_name,
    p.position,
    p.team_id,
    p.now_cost,
    p.status,
    p.chance_of_playing_next_round,
    pr.predicted_points
FROM players p
JOIN player_predictions pr ON pr.player_id = p.id
WHERE pr.season = '2026-27' AND pr.gameweek_id = 1;
"""


@dataclass
class PlayerRow:
    player_id: int
    web_name: str
    position: str
    team_id: int
    cost_tenths: int
    predicted_points: float
    status: str
    chance_of_playing: int | None


import pandas as pd

def load_candidates() -> list[PlayerRow]:
    df = pd.read_sql(text(QUERY), engine)

    rows = []
    for r in df.itertuples():
        chance = r.chance_of_playing_next_round
        if pd.isna(chance):
            chance = 0 if r.status in ("i", "s", "u") else 100
        availability_multiplier = chance / 100.0

        rows.append(PlayerRow(
            player_id=int(r.player_id),
            web_name=r.web_name,
            position=r.position,
            team_id=int(r.team_id),
            cost_tenths=round(r.now_cost * 10),
            predicted_points=float(r.predicted_points) * availability_multiplier,
            status=r.status,
            chance_of_playing=(None if pd.isna(r.chance_of_playing_next_round) else int(r.chance_of_playing_next_round)),        ))
    return rows


def solve_squad(players: list[PlayerRow]) -> list[PlayerRow]:
    model = cp_model.CpModel()
    picks = {p.player_id: model.NewBoolVar(f"pick_{p.player_id}") for p in players}

    model.Add(sum(picks.values()) == SQUAD_SIZE)
    model.Add(sum(picks[p.player_id] * p.cost_tenths for p in players) <= BUDGET)

    for pos, quota in POSITION_QUOTAS.items():
        model.Add(sum(picks[p.player_id] for p in players if p.position == pos) == quota)

    team_ids = {p.team_id for p in players}
    for team_id in team_ids:
        model.Add(sum(picks[p.player_id] for p in players if p.team_id == team_id) <= MAX_PER_CLUB)

    model.Maximize(sum(picks[p.player_id] * round(p.predicted_points * 1000) for p in players))

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("No feasible squad found — constraints may be infeasible.")

    return [p for p in players if solver.Value(picks[p.player_id]) == 1]


def print_squad(squad: list[PlayerRow]):
    total_cost = sum(p.cost_tenths for p in squad) / 10
    total_points = sum(p.predicted_points for p in squad)

    print(f"\nOptimal Squad — Budget used: £{total_cost:.1f}m / £100.0m | Predicted points: {total_points:.2f}\n")
    for pos in ["GKP", "DEF", "MID", "FWD"]:
        print(f"-- {pos} --")
        for p in sorted(squad, key=lambda x: -x.predicted_points):
            if p.position == pos:
                flag = f" [{p.status}, {p.chance_of_playing}%]" if p.status != "a" else ""
                print(f"  {p.web_name:20s} £{p.cost_tenths/10:.1f}m   pred: {p.predicted_points:.2f}{flag}")


if __name__ == "__main__":
    candidates = load_candidates()
    print(f"Loaded {len(candidates)} candidate players.")
    squad = solve_squad(candidates)
    print_squad(squad)