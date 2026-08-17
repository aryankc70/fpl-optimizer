from dataclasses import dataclass

from ortools.sat.python import cp_model

from fpl_optimizer.db.models import UserSquad
from fpl_optimizer.db.session import SessionLocal
from fpl_optimizer.optimization.squad_selector import (
    BUDGET, MAX_PER_CLUB, POSITION_QUOTAS, SQUAD_SIZE, PlayerRow, load_candidates,
)

HIT_COST = 4
MAX_SAVED_FREE_TRANSFERS = 5


@dataclass
class TransferSuggestion:
    new_squad: list[PlayerRow]
    transfers_out: list[PlayerRow]
    transfers_in: list[PlayerRow]
    num_transfers: int
    hits_taken: int
    hit_cost: int
    points_gained: float
    net_points_gained: float  # after hit cost


def get_current_squad_ids() -> set[int]:
    db = SessionLocal()
    try:
        squad = db.get(UserSquad, 1)
        if squad is None:
            raise RuntimeError("No squad found — run scripts/init_my_squad.py first.")
        return {int(pid) for pid in squad.player_ids.split(",")}
    finally:
        db.close()


def get_squad_state() -> UserSquad:
    db = SessionLocal()
    try:
        squad = db.get(UserSquad, 1)
        if squad is None:
            raise RuntimeError("No squad found — run scripts/init_my_squad.py first.")
        return squad
    finally:
        db.close()


def suggest_transfers(max_transfers: int | None = None) -> TransferSuggestion:
    """
    Solves for the best squad reachable from the CURRENT squad within a
    transfer budget — not a fresh from-scratch optimum. This is the key
    difference from squad_selector.solve_squad(): it adds a constraint
    limiting how many players can change, and only "spends" free transfers
    (or takes a hit) when the point gain justifies it.
    """
    current_ids = get_current_squad_ids()
    squad_state = get_squad_state()

    if max_transfers is None:
        max_transfers = squad_state.free_transfers

    candidates = load_candidates()
    candidate_by_id = {p.player_id: p for p in candidates}

    # Current squad's total spend — used to compute available budget alongside the bank
    current_squad_cost = sum(candidate_by_id[pid].cost_tenths for pid in current_ids if pid in candidate_by_id)
    available_budget = current_squad_cost + round(squad_state.bank * 10)

    model = cp_model.CpModel()
    picks = {p.player_id: model.NewBoolVar(f"pick_{p.player_id}") for p in candidates}

    model.Add(sum(picks.values()) == SQUAD_SIZE)
    model.Add(sum(picks[p.player_id] * p.cost_tenths for p in candidates) <= available_budget)

    for pos, quota in POSITION_QUOTAS.items():
        model.Add(sum(picks[p.player_id] for p in candidates if p.position == pos) == quota)

    team_ids = {p.team_id for p in candidates}
    for team_id in team_ids:
        model.Add(sum(picks[p.player_id] for p in candidates if p.team_id == team_id) <= MAX_PER_CLUB)

    # THE KEY CONSTRAINT: limit how many players can differ from the current squad.
    # A "kept" player is one who's both in the current squad AND picked again.
    kept_vars = [picks[pid] for pid in current_ids if pid in picks]
    num_kept = sum(kept_vars)
    model.Add(num_kept >= SQUAD_SIZE - max_transfers)

    # Maximize predicted points MINUS the hit cost for transfers beyond the free allowance.
    # transfers_used = SQUAD_SIZE - num_kept; hits = max(0, transfers_used - free_transfers)
    # CP-SAT can't directly maximize with a max() in the objective, so we model hits
    # as an auxiliary variable bounded appropriately.
    transfers_used = model.NewIntVar(0, SQUAD_SIZE, "transfers_used")
    model.Add(transfers_used == SQUAD_SIZE - num_kept)

    hits = model.NewIntVar(0, SQUAD_SIZE, "hits")
    model.Add(hits >= transfers_used - squad_state.free_transfers)
    model.Add(hits >= 0)

    total_predicted_points_scaled = sum(picks[p.player_id] * round(p.predicted_points * 1000) for p in candidates)
    hit_penalty_scaled = hits * HIT_COST * 1000

    model.Maximize(total_predicted_points_scaled - hit_penalty_scaled)

    solver = cp_model.CpSolver()
    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError("No feasible transfer plan found.")

    new_squad = [p for p in candidates if solver.Value(picks[p.player_id]) == 1]
    new_ids = {p.player_id for p in new_squad}

    transfers_out = [candidate_by_id[pid] for pid in current_ids if pid not in new_ids and pid in candidate_by_id]
    transfers_in = [p for p in new_squad if p.player_id not in current_ids]

    num_transfers = len(transfers_in)
    hits_taken = max(0, num_transfers - squad_state.free_transfers)
    hit_cost = hits_taken * HIT_COST

    old_points = sum(candidate_by_id[pid].predicted_points for pid in current_ids if pid in candidate_by_id)
    new_points = sum(p.predicted_points for p in new_squad)
    points_gained = new_points - old_points

    return TransferSuggestion(
        new_squad=new_squad,
        transfers_out=transfers_out,
        transfers_in=transfers_in,
        num_transfers=num_transfers,
        hits_taken=hits_taken,
        hit_cost=hit_cost,
        points_gained=points_gained,
        net_points_gained=points_gained - hit_cost,
    )


def print_suggestion(suggestion: TransferSuggestion):
    print(f"\nSuggested transfers: {suggestion.num_transfers} (hits: {suggestion.hits_taken}, cost: -{suggestion.hit_cost})")
    if suggestion.num_transfers == 0:
        print("No changes recommended — current squad is already optimal within transfer constraints.")
        return

    for out_p, in_p in zip(suggestion.transfers_out, suggestion.transfers_in):
        print(f"  OUT: {out_p.web_name:20s} ({out_p.predicted_points:.2f} pts)  ->  IN: {in_p.web_name:20s} ({in_p.predicted_points:.2f} pts)")

    print(f"\nPredicted points gained: {suggestion.points_gained:+.2f}")
    print(f"Net gain after hit cost: {suggestion.net_points_gained:+.2f}")



def apply_transfers() -> TransferSuggestion:
    """
    Recomputes the current best transfer suggestion server-side (never trusts
    a client-supplied plan, since predictions/squad could have changed) and
    commits it to UserSquad: new player list, updated bank, and free
    transfers rolled forward per the real FPL rule (unused transfers carry
    over, capped at 5; hits don't consume saved transfers, they cost points).
    """
    suggestion = suggest_transfers()

    db = SessionLocal()
    try:
        squad_state = db.get(UserSquad, 1)
        if squad_state is None:
            raise RuntimeError("No squad found — run scripts/init_my_squad.py first.")

        new_player_ids = ",".join(str(p.player_id) for p in suggestion.new_squad)
        new_total_cost = sum(p.cost_tenths for p in suggestion.new_squad) / 10

        old_squad_cost = sum(
            p.cost_tenths for p in load_candidates() if p.player_id in {int(x) for x in squad_state.player_ids.split(",")}
        ) / 10
        available_budget = old_squad_cost + squad_state.bank
        new_bank = round(available_budget - new_total_cost, 1)

        transfers_using_free = min(suggestion.num_transfers, squad_state.free_transfers)
        remaining_ft_stock = squad_state.free_transfers - transfers_using_free
        next_free_transfers = min(MAX_SAVED_FREE_TRANSFERS, remaining_ft_stock + 1)

        squad_state.player_ids = new_player_ids
        squad_state.bank = new_bank
        squad_state.free_transfers = next_free_transfers
        squad_state.last_updated_gameweek += 1
        db.commit()

        print(f"Applied {suggestion.num_transfers} transfer(s). New bank: £{new_bank}m, free transfers: {next_free_transfers}")
        return suggestion
    finally:
        db.close()


def advance_gameweek_no_transfer() -> dict:
    """
    For weeks where you choose not to act on any suggestion — rolls the
    free transfer forward (capped at 5) and advances the tracked gameweek,
    without changing the squad itself.
    """
    db = SessionLocal()
    try:
        squad_state = db.get(UserSquad, 1)
        if squad_state is None:
            raise RuntimeError("No squad found — run scripts/init_my_squad.py first.")

        squad_state.free_transfers = min(MAX_SAVED_FREE_TRANSFERS, squad_state.free_transfers + 1)
        squad_state.last_updated_gameweek += 1
        db.commit()

        # Read values out into plain data BEFORE the session closes — the
        # ORM object itself becomes unusable once its session is gone.
        return {
            "free_transfers": squad_state.free_transfers,
            "bank": squad_state.bank,
            "last_updated_gameweek": squad_state.last_updated_gameweek,
        }
    finally:
        db.close()


if __name__ == "__main__":
    suggestion = suggest_transfers()
    print_suggestion(suggestion)