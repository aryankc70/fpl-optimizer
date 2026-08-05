import math
from dataclasses import dataclass
from sqlalchemy import text
from fpl_optimizer.db.session import engine

# 2025-26 Premier League averaged 2.75 goals per match (1,045 goals / 380 matches),
# so ~1.375 goals per team per match — our league-average anchor for the Poisson rate.
LEAGUE_AVG_GOALS_PER_TEAM = 1.375

TEAM_STRENGTH_QUERY = """
SELECT id, strength_overall_home, strength_overall_away,
       strength_attack_home, strength_attack_away,
       strength_defence_home, strength_defence_away
FROM teams WHERE id = :team_id;
"""


@dataclass
class CleanSheetEstimate:
    expected_goals_conceded: float
    clean_sheet_probability: float
    method: str  # tells us which data source was actually used


def _get_team_strength(team_id: int) -> dict:
    with engine.connect() as conn:
        row = conn.execute(text(TEAM_STRENGTH_QUERY), {"team_id": team_id}).fetchone()
    return dict(row._mapping) if row else {}


def estimate_clean_sheet(defending_team_id: int, opponent_team_id: int, defending_team_is_home: bool) -> CleanSheetEstimate:
    """
    Estimates a team's clean-sheet probability for one fixture using a Poisson
    model: goals conceded ~ Poisson(lambda), where lambda is derived from
    relative team strength.

    Uses the granular attack/defence strength splits when FPL has populated
    them (mid-season onward); falls back to the always-available overall
    home/away strength ratings otherwise (e.g. pre-season, when splits are 0).
    """
    defending = _get_team_strength(defending_team_id)
    opponent = _get_team_strength(opponent_team_id)

    def_attack_split_available = (
        opponent.get("strength_attack_home", 0) and opponent.get("strength_attack_away", 0)
        and defending.get("strength_defence_home", 0) and defending.get("strength_defence_away", 0)
    )

    if def_attack_split_available:
        opponent_attack = opponent["strength_attack_away"] if defending_team_is_home else opponent["strength_attack_home"]
        defending_defence = defending["strength_defence_home"] if defending_team_is_home else defending["strength_defence_away"]
        method = "attack_defence_split"
    else:
        # Fallback: overall strength as a blended proxy for both attack and
        # defence quality — less precise, but real, current data rather than
        # a guess. Documented limitation: this can't isolate a team's
        # defensive solidity from its attacking output.
        opponent_attack = opponent.get("strength_overall_away", 3) if defending_team_is_home else opponent.get("strength_overall_home", 3)
        defending_defence = defending.get("strength_overall_home", 3) if defending_team_is_home else defending.get("strength_overall_away", 3)
        method = "overall_strength_fallback"

    # Guard against zero/missing data
    opponent_attack = opponent_attack or 3
    defending_defence = defending_defence or 3

    expected_goals_conceded = LEAGUE_AVG_GOALS_PER_TEAM * (opponent_attack / defending_defence)
    clean_sheet_probability = math.exp(-expected_goals_conceded)  # Poisson P(X = 0)

    return CleanSheetEstimate(
        expected_goals_conceded=round(expected_goals_conceded, 3),
        clean_sheet_probability=round(clean_sheet_probability, 3),
        method=method,
    )


if __name__ == "__main__":
    from fpl_optimizer.db.session import SessionLocal
    from fpl_optimizer.db.models import Team

    db = SessionLocal()
    arsenal = db.query(Team).filter_by(name="Arsenal").first()
    brighton = db.query(Team).filter_by(name="Brighton").first()
    db.close()

    est = estimate_clean_sheet(defending_team_id=arsenal.id, opponent_team_id=brighton.id, defending_team_is_home=True)
    print(f"Arsenal (home) vs Brighton — method: {est.method}")
    print(f"Expected goals conceded: {est.expected_goals_conceded}")
    print(f"Clean sheet probability: {est.clean_sheet_probability * 100:.1f}%")