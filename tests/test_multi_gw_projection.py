import math

from fpl_optimizer.features.clean_sheet_model import estimate_clean_sheet


def test_clean_sheet_probability_is_valid_probability(monkeypatch):
    """Regardless of inputs, clean sheet probability must be a valid 0-1 value."""
    def fake_get_team_strength(team_id):
        return {
            "strength_overall_home": 3, "strength_overall_away": 3,
            "strength_attack_home": 0, "strength_attack_away": 0,
            "strength_defence_home": 0, "strength_defence_away": 0,
        }

    import fpl_optimizer.features.clean_sheet_model as csm
    monkeypatch.setattr(csm, "_get_team_strength", fake_get_team_strength)

    est = estimate_clean_sheet(defending_team_id=1, opponent_team_id=2, defending_team_is_home=True)
    assert 0 <= est.clean_sheet_probability <= 1
    assert est.expected_goals_conceded > 0


def test_poisson_formula_matches_manual_calculation(monkeypatch):
    def fake_get_team_strength(team_id):
        return {
            "strength_overall_home": 3, "strength_overall_away": 3,
            "strength_attack_home": 0, "strength_attack_away": 0,
            "strength_defence_home": 0, "strength_defence_away": 0,
        }

    import fpl_optimizer.features.clean_sheet_model as csm
    monkeypatch.setattr(csm, "_get_team_strength", fake_get_team_strength)

    est = estimate_clean_sheet(defending_team_id=1, opponent_team_id=2, defending_team_is_home=True)
    # Equal strength (3 vs 3) means the multiplier should be neutral (~1.0x league average)
    expected = 1.375 * (3 / 3)
    assert abs(est.expected_goals_conceded - expected) < 0.01
    assert abs(est.clean_sheet_probability - math.exp(-expected)) < 0.001