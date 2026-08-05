from sqlalchemy import text
from fpl_optimizer.db.session import engine

# Difficulty is 1 (easiest) to 5 (hardest) in FPL's own scale.
# We convert it into a multiplier: difficulty 3 (average) = 1.0x,
# each step away from 3 nudges the projection up/down by 8%.
DIFFICULTY_BASELINE = 3
ADJUSTMENT_PER_STEP = 0.08

FIXTURES_QUERY = """
SELECT
    f.gameweek_id,
    f.team_h_id,
    f.team_a_id,
    f.team_h_difficulty,
    f.team_a_difficulty
FROM fixtures f
WHERE f.gameweek_id BETWEEN :start_gw AND :end_gw;
"""


def get_team_fixture_difficulty(start_gw: int, n_weeks: int = 3) -> dict[int, list[int]]:
    """Returns {team_id: [difficulty_gw1, difficulty_gw2, ...]} for the given window."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(FIXTURES_QUERY),
            {"start_gw": start_gw, "end_gw": start_gw + n_weeks - 1},
        ).fetchall()

    team_difficulty: dict[int, list[int]] = {}
    for r in rows:
        team_difficulty.setdefault(r.team_h_id, []).append(r.team_h_difficulty)
        team_difficulty.setdefault(r.team_a_id, []).append(r.team_a_difficulty)
    return team_difficulty


def project_multi_gw_points(base_weekly_prediction: float, team_id: int, start_gw: int, n_weeks: int = 3) -> float:
    """
    Projects total points over n_weeks by applying a fixture-difficulty
    multiplier to the model's base weekly prediction for each fixture in
    the window. A team with 2 fixtures in a gameweek (double gameweek)
    naturally gets counted twice, which is correct — more games, more
    expected points.
    """
    difficulties = get_team_fixture_difficulty(start_gw, n_weeks).get(team_id, [])

    total = 0.0
    for diff in difficulties:
        multiplier = 1.0 - (diff - DIFFICULTY_BASELINE) * ADJUSTMENT_PER_STEP
        total += base_weekly_prediction * multiplier

    return total