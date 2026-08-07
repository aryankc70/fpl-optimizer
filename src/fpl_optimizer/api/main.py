from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from fpl_optimizer.db.session import engine
from fpl_optimizer.optimization.squad_selector import load_candidates, solve_squad
from fpl_optimizer.optimization.lineup_selector import solve_lineup
from fpl_optimizer.optimization.hit_advisor import evaluate_hit
from fpl_optimizer.optimization.chip_calendar import get_current_guidance
from fpl_optimizer.api.schemas import (
    PlayerPredictionOut, SquadOut, SquadPlayerOut, LineupOut,
    HitEvaluationRequest, HitEvaluationOut, ChipGuidanceOut,
)

app = FastAPI(title="FPL Optimizer API", version="1.0.0")

CURRENT_SEASON = "2026-27"


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/predictions/{gameweek}", response_model=list[PlayerPredictionOut])
def get_predictions(gameweek: int):
    query = text("""
        SELECT p.id AS player_id, p.web_name, p.position, t.name AS team_name,
               p.now_cost, pr.predicted_points, p.status, p.chance_of_playing_next_round AS chance_of_playing
        FROM player_predictions pr
        JOIN players p ON p.id = pr.player_id
        JOIN teams t ON t.id = p.team_id
        WHERE pr.season = :season AND pr.gameweek_id = :gw
        ORDER BY pr.predicted_points DESC;
    """)
    with engine.connect() as conn:
        rows = conn.execute(query, {"season": CURRENT_SEASON, "gw": gameweek}).mappings().all()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No predictions found for gameweek {gameweek}")
    return list(rows)


@app.get("/players/{player_id}", response_model=PlayerPredictionOut)
def get_player(player_id: int, gameweek: int = 1):
    query = text("""
        SELECT p.id AS player_id, p.web_name, p.position, t.name AS team_name,
               p.now_cost, pr.predicted_points, p.status, p.chance_of_playing_next_round AS chance_of_playing
        FROM players p
        JOIN teams t ON t.id = p.team_id
        LEFT JOIN player_predictions pr
            ON pr.player_id = p.id AND pr.season = :season AND pr.gameweek_id = :gw
        WHERE p.id = :player_id;
    """)
    with engine.connect() as conn:
        row = conn.execute(query, {"player_id": player_id, "season": CURRENT_SEASON, "gw": gameweek}).mappings().first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Player {player_id} not found")
    return row


@app.get("/squad/optimal", response_model=SquadOut)
def get_optimal_squad():
    candidates = load_candidates()
    squad = solve_squad(candidates)
    return SquadOut(
        total_cost=sum(p.cost_tenths for p in squad) / 10,
        total_predicted_points=sum(p.predicted_points for p in squad),
        players=[
            SquadPlayerOut(
                player_id=p.player_id, web_name=p.web_name, position=p.position,
                cost=p.cost_tenths / 10, predicted_points=p.predicted_points, status=p.status,
            )
            for p in squad
        ],
    )


@app.get("/lineup/optimal", response_model=LineupOut)
def get_optimal_lineup():
    candidates = load_candidates()
    squad = solve_squad(candidates)
    starting_xi, captain, vice_captain = solve_lineup(squad)
    bench = [p for p in squad if p not in starting_xi]

    formation = {pos: sum(1 for p in starting_xi if p.position == pos) for pos in ["DEF", "MID", "FWD"]}
    formation_str = f"{formation['DEF']}-{formation['MID']}-{formation['FWD']}"

    base_points = sum(p.predicted_points for p in starting_xi)

    def to_out(p):
        return SquadPlayerOut(
            player_id=p.player_id, web_name=p.web_name, position=p.position,
            cost=p.cost_tenths / 10, predicted_points=p.predicted_points, status=p.status,
        )

    return LineupOut(
        formation=formation_str,
        starting_xi=[to_out(p) for p in starting_xi],
        bench=[to_out(p) for p in bench],
        captain=to_out(captain),
        vice_captain=to_out(vice_captain),
        base_points=base_points,
        points_with_captain=base_points + captain.predicted_points,
    )


@app.post("/hit-advisor", response_model=HitEvaluationOut)
def hit_advisor(request: HitEvaluationRequest):
    try:
        rec = evaluate_hit(
            outgoing_player_id=request.outgoing_player_id,
            incoming_player_id=request.incoming_player_id,
            num_hits=request.num_hits,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return HitEvaluationOut(**rec.__dict__)


@app.get("/chip-calendar/{gameweek}", response_model=ChipGuidanceOut)
def chip_calendar(gameweek: int):
    windows = get_current_guidance(gameweek)
    return ChipGuidanceOut(
        gameweek=gameweek,
        windows=[
            {"phase": w.phase, "focus": w.focus, "guidance": w.guidance}
            for w in windows
        ],
    )