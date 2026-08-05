from dataclasses import dataclass


@dataclass
class ChipWindow:
    gw_start: int
    gw_end: int
    phase: str
    focus: str
    guidance: str


# Static reference calendar derived from the 2026/27 season roadmap.
# NOTE: blank/double gameweek predictions are estimates based on historical
# cup scheduling patterns, not confirmed fixtures — always cross-check
# against the official fixture list before actually using a chip.
CHIP_CALENDAR: list[ChipWindow] = [
    ChipWindow(1, 5, "Foundation", "Initial draft & layups",
               "Build around high xG/xA players with favorable opening fixtures. Avoid differentials for their own sake."),
    ChipWindow(6, 6, "First Pivot", "Wildcard 1 window",
               "Primary Wildcard 1 window — use the long international break to reset for the next 8-10 GWs."),
    ChipWindow(7, 7, "First Pivot", "Captaincy hunt",
               "Start hunting captaincy based on Threat index. Only go differential if the template captain has a tough fixture."),
    ChipWindow(9, 9, "First Pivot", "Alternative WC window",
               "Secondary Wildcard 1 window if not used at GW6 and squad structure is off-template."),
    ChipWindow(10, 12, "First Pivot", "Template consolidation",
               "Protect rank with high-ownership, strong-xG players. Avoid unnecessary hits."),
    ChipWindow(13, 18, "Festive Chaos", "Bench strength & layups",
               "Winter fixture congestion — ensure players 12-13 in your squad are rotation-safe, not just cheap fodder."),
    ChipWindow(19, 20, "Festive Chaos", "Wildcard 2 window",
               "Use Wildcard 2 if team value is lagging or a major structural overhaul is needed."),
    ChipWindow(21, 22, "Festive Chaos", "Cup blanks foresight",
               "Start preparing for the Carabao Cup final blank (est. GW24-25) by targeting players guaranteed to play."),
    ChipWindow(23, 29, "Chip Runway", "Blank GW preparation",
               "Build toward the first major blank gameweek — prioritize players confirmed to have a fixture."),
    ChipWindow(30, 30, "Chip Runway", "Predicted blank GW — Free Hit target",
               "Estimated Blank Gameweek (Carabao Cup final). Prime Free Hit candidate if 3+ starters are missing a fixture."),
    ChipWindow(33, 33, "Chip Runway", "Predicted mega double GW — Bench Boost target",
               "Estimated biggest Double Gameweek. Prime Bench Boost window — target 12-13 strong starters, not 15 forced doublers."),
    ChipWindow(34, 34, "Chip Runway", "FA Cup blanks navigation",
               "Navigate via transfers or a late Wildcard if unused. Prioritize confirmed fixtures."),
    ChipWindow(36, 37, "Chip Runway", "Predicted final double GW — Triple Captain target",
               "Estimated final Double Gameweek. Prime Triple Captain window for a premium player (based on Threat + fixture)."),
    ChipWindow(38, 38, "Chip Runway", "The final push",
               "One-week shootout — maximize expected points with no need to protect future team value."),
]


def get_current_guidance(gw: int) -> list[ChipWindow]:
    """A gameweek can fall into more than one window (e.g. overlapping focus areas)."""
    return [w for w in CHIP_CALENDAR if w.gw_start <= gw <= w.gw_end]


def print_guidance(gw: int):
    windows = get_current_guidance(gw)
    if not windows:
        print(f"No specific guidance recorded for GW{gw}.")
        return

    print(f"\n=== Chip Strategy Guidance — Gameweek {gw} ===")
    for w in windows:
        print(f"\nPhase: {w.phase}")
        print(f"Focus: {w.focus}")
        print(f"Guidance: {w.guidance}")


if __name__ == "__main__":
    for test_gw in [1, 6, 20, 33, 38]:
        print_guidance(test_gw)