from fpl_optimizer.optimization.chip_calendar import get_current_guidance


def test_gw6_flags_wildcard_window():
    windows = get_current_guidance(6)
    assert any("Wildcard 1" in w.focus for w in windows)


def test_gw33_flags_bench_boost():
    windows = get_current_guidance(33)
    assert any("Bench Boost" in w.focus for w in windows)


def test_gw38_flags_final_push():
    windows = get_current_guidance(38)
    assert any("final push" in w.focus.lower() for w in windows)


def test_unlisted_gameweek_returns_empty():
    # GW 39 doesn't exist in a 38-week season — should return no guidance, not crash
    windows = get_current_guidance(39)
    assert windows == []