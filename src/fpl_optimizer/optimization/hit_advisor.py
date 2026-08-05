from dataclasses import dataclass
from sqlalchemy import text
from fpl_optimizer.db.session import engine, SessionLocal
from fpl_optimizer.db.models import Player
from fpl_optimizer.optimization.multi_gw_projection import project_multi_gw_points

HIT_COST = 4  # standard FPL cost for one extra transfer
OUTSCORE_THRESHOLD = 4  # from the "3-week outscore rule"

PREDICTION_QUERY = """
SELECT predicted_points FROM player_predictions
WHERE player_id = :player_id AND season = :season AND gameweek_id = :gw;
"""


@dataclass
class HitRecommendation:
    outgoing_name: str
    incoming_name: str
    outgoing_3gw_projection: float
    incoming_3gw_projection: float
    net_gain: float
    hit_cost: int
    recommendation: str
    reasoning: str


def get_base_prediction(player_id: int, season: str, gw: int) -> float:
    with engine.connect() as conn:
        row = conn.execute(
            text(PREDICTION_QUERY),
            {"player_id": player_id, "season": season, "gw": gw},
        ).fetchone()
    return row.predicted_points if row else 0.0


def evaluate_hit(
    outgoing_player_id: int,
    incoming_player_id: int,
    start_gw: int = 1,
    season: str = "2026-27",
    n_weeks: int = 3,
    num_hits: int = 1,
) -> HitRecommendation:
    db = SessionLocal()
    try:
        outgoing = db.get(Player, outgoing_player_id)
        incoming = db.get(Player, incoming_player_id)

        out_base = get_base_prediction(outgoing_player_id, season, start_gw)
        in_base = get_base_prediction(incoming_player_id, season, start_gw)

        out_proj = project_multi_gw_points(out_base, outgoing.team_id, start_gw, n_weeks)
        in_proj = project_multi_gw_points(in_base, incoming.team_id, start_gw, n_weeks)

        total_hit_cost = HIT_COST * num_hits
        net_gain = in_proj - out_proj - total_hit_cost

        # The "4+ point outscore over 3 GWs" rule, applied AFTER accounting for the hit cost itself
        if net_gain >= OUTSCORE_THRESHOLD:
            recommendation = "TAKE THE HIT"
            reasoning = (
                f"{incoming.web_name} projects {in_proj - out_proj:.1f} pts higher than "
                f"{outgoing.web_name} over {n_weeks} GWs, clearing the hit cost "
                f"(-{total_hit_cost}) with {net_gain:.1f} pts to spare."
            )
        elif net_gain >= 0:
            recommendation = "MARGINAL — CONSIDER WAITING"
            reasoning = (
                f"Net gain after hit cost is only {net_gain:.1f} pts — positive, but below "
                f"the {OUTSCORE_THRESHOLD}-pt threshold. The 'Layup Principle' favors patience here."
            )
        else:
            recommendation = "DO NOT TAKE THE HIT"
            reasoning = (
                f"{incoming.web_name} does not project to outscore {outgoing.web_name} "
                f"enough to justify the {total_hit_cost}-pt cost (net: {net_gain:.1f} pts)."
            )

        return HitRecommendation(
            outgoing_name=outgoing.web_name,
            incoming_name=incoming.web_name,
            outgoing_3gw_projection=out_proj,
            incoming_3gw_projection=in_proj,
            net_gain=net_gain,
            hit_cost=total_hit_cost,
            recommendation=recommendation,
            reasoning=reasoning,
        )
    finally:
        db.close()


def print_recommendation(rec: HitRecommendation):
    print(f"\n--- Hit Evaluation: {rec.outgoing_name} -> {rec.incoming_name} ---")
    print(f"{rec.outgoing_name} (3-GW projection): {rec.outgoing_3gw_projection:.2f}")
    print(f"{rec.incoming_name} (3-GW projection): {rec.incoming_3gw_projection:.2f}")
    print(f"Hit cost: -{rec.hit_cost}")
    print(f"Net gain: {rec.net_gain:.2f}")
    print(f"\n>>> {rec.recommendation}")
    print(f"    {rec.reasoning}")


if __name__ == "__main__":
    db = SessionLocal()
    # Example: evaluate swapping a mid-priced player for a pricier in-form one
    p1 = db.query(Player).filter_by(web_name="Watkins").first()
    p2 = db.query(Player).filter_by(web_name="Thiago").first()
    db.close()

    rec = evaluate_hit(outgoing_player_id=p1.id, incoming_player_id=p2.id)
    print_recommendation(rec)