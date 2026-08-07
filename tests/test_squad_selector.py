from fpl_optimizer.optimization.squad_selector import (
    BUDGET,
    MAX_PER_CLUB,
    POSITION_QUOTAS,
    PlayerRow,
    solve_squad,
)


def make_candidates():
    """A small synthetic player pool, cheap enough to make the constraints
    actually bind (forces the solver to make real tradeoffs, not just pick everyone)."""
    candidates = []
    pid = 1
    for team_id in range(1, 6):  # 5 fake clubs
        for pos, count, cost, points in [
            ("GKP", 3, 45, 4.0),
            ("DEF", 6, 50, 4.0),
            ("MID", 6, 55, 4.0),
            ("FWD", 4, 60, 4.0),
        ]:
            for i in range(count):
                candidates.append(PlayerRow(
                    player_id=pid,
                    web_name=f"Player{pid}",
                    position=pos,
                    team_id=team_id,
                    cost_tenths=cost + i,  # slight variation so costs aren't identical
                    predicted_points=points + (i * 0.1),
                    status="a",
                    chance_of_playing=100,
                ))
                pid += 1
    return candidates


def test_squad_respects_budget():
    squad = solve_squad(make_candidates())
    total_cost = sum(p.cost_tenths for p in squad)
    assert total_cost <= BUDGET


def test_squad_has_correct_size():
    squad = solve_squad(make_candidates())
    assert len(squad) == 15


def test_squad_respects_position_quotas():
    squad = solve_squad(make_candidates())
    for pos, quota in POSITION_QUOTAS.items():
        count = sum(1 for p in squad if p.position == pos)
        assert count == quota, f"Expected {quota} {pos}, got {count}"


def test_squad_respects_club_limit():
    squad = solve_squad(make_candidates())
    from collections import Counter
    club_counts = Counter(p.team_id for p in squad)
    for team_id, count in club_counts.items():
        assert count <= MAX_PER_CLUB, f"Team {team_id} has {count} players, exceeds max {MAX_PER_CLUB}"


def test_squad_is_infeasible_with_impossible_budget():
    """Sanity check: if the budget is absurdly low, the solver should raise
    rather than silently returning an invalid squad."""
    candidates = make_candidates()
    import fpl_optimizer.optimization.squad_selector as ss
    original_budget = ss.BUDGET
    ss.BUDGET = 1  # impossible
    try:
        with __import__("pytest").raises(RuntimeError):
            solve_squad(candidates)
    finally:
        ss.BUDGET = original_budget