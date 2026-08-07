from ortools.sat.python import cp_model

from fpl_optimizer.optimization.squad_selector import PlayerRow

FORMATION_LIMITS = {
    "DEF": (3, 5),
    "MID": (2, 5),
    "FWD": (1, 3),
}
STARTING_XI_SIZE = 11
STARTING_GKP = 1


def solve_lineup(squad: list[PlayerRow]) -> tuple[list[PlayerRow], PlayerRow, PlayerRow]:
    model = cp_model.CpModel()

    starts = {p.player_id: model.NewBoolVar(f"start_{p.player_id}") for p in squad}

    # Exactly 11 starters
    model.Add(sum(starts.values()) == STARTING_XI_SIZE)

    # Exactly 1 goalkeeper starts
    model.Add(sum(starts[p.player_id] for p in squad if p.position == "GKP") == STARTING_GKP)

    # Formation bounds for outfield positions
    for pos, (min_count, max_count) in FORMATION_LIMITS.items():
        pos_sum = sum(starts[p.player_id] for p in squad if p.position == pos)
        model.Add(pos_sum >= min_count)
        model.Add(pos_sum <= max_count)

    # Maximize predicted points of the starting XI (captain bonus handled separately below,
    # since captaincy is just "double the single best starter's points" — a simpler
    # follow-up calculation rather than another full ILP)
    model.Maximize(
        sum(starts[p.player_id] * round(p.predicted_points * 1000) for p in squad)
    )

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("No feasible lineup found.")

    starting_xi = [p for p in squad if solver.Value(starts[p.player_id]) == 1]

    # Captain = highest predicted points in the starting XI (their points double).
    # Vice-captain = second highest (backup armband if captain doesn't play).
    ranked = sorted(starting_xi, key=lambda p: -p.predicted_points)
    captain, vice_captain = ranked[0], ranked[1]

    return starting_xi, captain, vice_captain


def print_lineup(squad: list[PlayerRow], starting_xi: list[PlayerRow], captain: PlayerRow, vice_captain: PlayerRow):
    bench = [p for p in squad if p not in starting_xi]

    formation = {
        pos: sum(1 for p in starting_xi if p.position == pos)
        for pos in ["DEF", "MID", "FWD"]
    }
    formation_str = f"{formation['DEF']}-{formation['MID']}-{formation['FWD']}"

    base_points = sum(p.predicted_points for p in starting_xi)
    total_with_captain = base_points + captain.predicted_points  # captain's points counted again (doubled)

    print(f"\nStarting XI — Formation {formation_str}")
    print(f"Base predicted points: {base_points:.2f} | With captain bonus: {total_with_captain:.2f}\n")

    for pos in ["GKP", "DEF", "MID", "FWD"]:
        print(f"-- {pos} --")
        for p in sorted(starting_xi, key=lambda x: -x.predicted_points):
            if p.position == pos:
                tag = " (C)" if p.player_id == captain.player_id else " (VC)" if p.player_id == vice_captain.player_id else ""
                print(f"  {p.web_name:20s} pred: {p.predicted_points:.2f}{tag}")

    print("\n-- Bench --")
    for p in sorted(bench, key=lambda x: -x.predicted_points):
        print(f"  {p.web_name:20s} pred: {p.predicted_points:.2f}")


if __name__ == "__main__":
    from fpl_optimizer.optimization.squad_selector import load_candidates, solve_squad

    candidates = load_candidates()
    squad = solve_squad(candidates)
    starting_xi, captain, vice_captain = solve_lineup(squad)
    print_lineup(squad, starting_xi, captain, vice_captain)